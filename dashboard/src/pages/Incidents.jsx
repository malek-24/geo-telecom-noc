import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  ShieldCheck, CheckCircle2, Clock, AlertTriangle, XCircle,
  ChevronDown, ChevronUp, RefreshCw, MessageSquare, Wrench,
  UserCheck, Activity, Wifi, Thermometer, Cpu, Zap, Download
} from 'lucide-react';
import axios from 'axios';
import Sidebar from '../components/Sidebar';
import { API_BASE_URL, authCfg } from '../services/apiConfig';
import { downloadCsv } from '../services/exportCsv';
import { useAuth } from '../auth/AuthContext';
import { REFRESH_MS } from '../dataRefreshMs';
import { mergeById } from '../utils/silentRefresh';
import { formatDateTimeTN, parseServerDate } from '../utils/dateTime';
import './IncidentsPage.css';

/* ── Helpers ─────────────────────────────────────────────── */
const ROLE_LABELS = {
  administrateur:     { label: 'Admin',      color: '#2563eb' },
  ingenieur_reseau:   { label: 'Ingénieur',  color: '#7c3aed' },
  technicien_terrain: { label: 'Technicien', color: '#d97706' },
};

const METRIC_ICONS = {
  temperature:  <Thermometer size={12}/>,
  cpu:          <Cpu size={12}/>,
  signal:       <Wifi size={12}/>,
  latence:      <Activity size={12}/>,
  disponibilite:<Zap size={12}/>,
};

const METRIC_UNITS = {
  temperature: '°C', cpu: '%', signal: ' dBm',
  latence: ' ms', disponibilite: '%', risk_score: '%',
};

function elapsedStr(d) {
  if (!d) return '—';
  const parsed = parseServerDate(d);
  if (!parsed) return '—';
  const ms = Date.now() - parsed.getTime();
  const h = Math.floor(ms / 3600000);
  const m = Math.floor((ms % 3600000) / 60000);
  return h > 0 ? `${h}h ${m}min` : `${m} min`;
}

/* ── Toast de notification ───────────────────────────────── */
function Toast({ toast, onClose }) {
  useEffect(() => {
    if (!toast) return;
    const t = setTimeout(onClose, 5000);
    return () => clearTimeout(t);
  }, [toast, onClose]);

  if (!toast) return null;
  const isSuccess = toast.type === 'success';
  return (
    <div style={{
      position: 'fixed', bottom: 28, right: 28, zIndex: 9999,
      background: isSuccess ? 'var(--success-bg, #f0fdf4)' : 'var(--warning-bg, #fffbeb)',
      border: `1.5px solid ${isSuccess ? 'var(--success, #22c55e)' : 'var(--warning, #f59e0b)'}`,
      borderRadius: 10, padding: '14px 20px', maxWidth: 380,
      boxShadow: '0 8px 32px rgba(0,0,0,0.18)',
      display: 'flex', alignItems: 'flex-start', gap: 12,
      animation: 'slideInRight 0.3s ease',
    }}>
      {isSuccess
        ? <CheckCircle2 size={20} color="var(--success, #22c55e)" style={{ flexShrink: 0, marginTop: 2 }} />
        : <AlertTriangle size={20} color="var(--warning, #f59e0b)" style={{ flexShrink: 0, marginTop: 2 }} />
      }
      <div style={{ flex: 1 }}>
        <div style={{ fontWeight: 700, fontSize: '0.9rem', color: isSuccess ? 'var(--success, #15803d)' : '#92400e', marginBottom: 4 }}>
          {isSuccess ? '✅ Incident résolu' : '⚠️ Anomalie persistante'}
        </div>
        <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)', lineHeight: 1.5 }}>
          {toast.message}
        </div>
      </div>
      <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-light)', padding: 2, flexShrink: 0 }}>
        <XCircle size={16} />
      </button>
    </div>
  );
}

/* ── Page principale ─────────────────────────────────────── */
export default function IncidentsPage() {
  const { token, role } = useAuth();
  const [incidents, setIncidents] = useState([]);
  const [loading,   setLoading]   = useState(true);
  const [expanded,  setExpanded]  = useState(null);
  const [filter,    setFilter]    = useState('tous');
  const [resolving, setResolving] = useState(null);
  const [comments,  setComments]  = useState([]);
  const [newComment,setNewComment]= useState('');
  const [newEtat,   setNewEtat]   = useState('en_cours');
  const [sending,   setSending]   = useState(false);
  const [toast,     setToast]     = useState(null);
  const [exporting, setExporting] = useState(false);

  const canResolve = ['administrateur', 'ingenieur_reseau'].includes(role);

  const handleExportCsv = async () => {
    setExporting(true);
    try {
      await downloadCsv(token, '/export/incidents', 'export_incidents.csv');
    } catch (_) {
      setToast({ type: 'warning', message: 'Erreur lors de l\'export CSV.' });
    } finally {
      setExporting(false);
    }
  };

  const initialLoad = useRef(true);

  const fetchIncidents = useCallback(async () => {
    if (!token) return;
    try {
      const r = await axios.get(`${API_BASE_URL}/incidents`, authCfg(token));
      setIncidents(prev => mergeById(prev, r.data));
    } catch (_) {}
    finally {
      if (initialLoad.current) {
        setLoading(false);
        initialLoad.current = false;
      }
    }
  }, [token]);

  useEffect(() => {
    fetchIncidents();
    const id = setInterval(fetchIncidents, REFRESH_MS.incidents);
    return () => clearInterval(id);
  }, [fetchIncidents]);

  const handleResolve = async (id) => {
    setResolving(id);

    // ── Optimistic update : marquer immédiatement dans l'UI ────────
    // Les données historiques (métriques, graphiques, scores) ne sont pas touchées.
    // Seul le statut affiché change en attendant la réponse serveur.
    setIncidents(prev => prev.map(inc =>
      inc.id === id
        ? { ...inc, statut: 'resolu', date_resolution: new Date().toISOString() }
        : inc
    ));

    try {
      const res = await axios.put(
        `${API_BASE_URL}/incidents/${id}/resolve`,
        {},
        authCfg(token)
      );

      const data = res.data;

      // ── Toast selon le résultat de la validation IA ────────────
      if (data.resolution_validee) {
        setToast({
          type: 'success',
          message:
            data.message ||
            'Antenne → normal, score santé = 95. ' +
            'Historique des mesures, graphiques et scores conservés.'
        });
      } else if (data.success) {
        setToast({
          type: 'warning',
          message:
            data.message ||
            `Anomalie persistante détectée. Nouvel incident #${data.nouvel_incident_id || '?'} créé.`
        });
      }

      // ── Rafraîchissement complet depuis le serveur ─────────────
      await fetchIncidents();

    } catch (err) {
      // Annuler l'optimistic update en cas d'échec réseau
      await fetchIncidents();
      setToast({
        type: 'warning',
        message: err.response?.data?.error || 'Erreur lors de la résolution de l\'incident.'
      });
    }
    setResolving(null);
  };

  const loadComments = async (incId) => {
    try {
      const r = await axios.get(`${API_BASE_URL}/incidents/${incId}/commentaires`,
        authCfg(token));
      setComments(r.data);
    } catch (_) {}
  };

  const handleExpand = (id) => {
    if (expanded === id) { setExpanded(null); return; }
    setExpanded(id); setComments([]); loadComments(id);
  };

  const handlePostComment = async (incId) => {
    if (!newComment.trim()) return;
    setSending(true);
    try {
      await axios.post(`${API_BASE_URL}/incidents/${incId}/commentaires`,
        { contenu: newComment, etat_resolution: newEtat },
        authCfg(token));
      setNewComment(''); setNewEtat('en_cours');
      await loadComments(incId);
      if (newEtat === 'réglé') await fetchIncidents();
    } catch (e) { alert(e.response?.data?.error || 'Erreur.'); }
    finally { setSending(false); }
  };

  const stats = {
    total:    incidents.length,
    actifs:   incidents.filter(i => i.statut === 'en_cours').length,
    resolus:  incidents.filter(i => i.statut === 'resolu').length,
    critiques:incidents.filter(i => i.criticite === 'critical').length,
  };

  const FILTERS = [
    { key: 'tous',     label: 'Tous',      count: stats.total },
    { key: 'en_cours', label: 'En cours',  count: stats.actifs },
    { key: 'resolu',   label: 'Résolus',   count: stats.resolus },
    { key: 'critical', label: 'Critiques', count: stats.critiques },
  ];

  const filtered = incidents.filter(inc =>
    filter === 'tous'     ? true :
    filter === 'critical' ? inc.criticite === 'critical' :
    inc.statut === filter
  );

  if (loading) return (
    <div style={{ display: 'flex' }}>
      <Sidebar />
      <div className="loading-center" style={{ flex: 1 }}>
        <div className="spinner" />
        <span>Chargement des incidents…</span>
      </div>
    </div>
  );

  return (
    <div style={{ display: 'flex' }}>
      <Sidebar />

      {/* ── Toast de résolution ── */}
      <Toast toast={toast} onClose={() => setToast(null)} />

      {/* Animation CSS pour le toast */}
      <style>{`
        @keyframes slideInRight {
          from { transform: translateX(120%); opacity: 0; }
          to   { transform: translateX(0);    opacity: 1; }
        }
      `}</style>

      <div className="page-content">
        <div className="ip-shell">

          {/* ── EN-TÊTE ── */}
          <div className="ip-header">
            <div>
              <h1 className="ip-title">
                {role === 'technicien_terrain'
                  ? <><Wrench size={20} /> Interventions Terrain</>
                  : <><ShieldCheck size={20} /> Gestion des Incidents</>
                }
              </h1>
            </div>
            <div style={{ display: 'flex', gap: 8 }}>
              <button type="button" className="btn btn-secondary" onClick={handleExportCsv} disabled={exporting}>
                <Download size={14} /> {exporting ? 'Export…' : 'Exporter CSV'}
              </button>
              <button className="btn btn-secondary" onClick={fetchIncidents}>
                <RefreshCw size={14} /> Actualiser
              </button>
            </div>
          </div>

          {/* ── STATISTIQUES ── */}
          <div className="ip-stats-row">
            <div className="ip-stat ip-stat--blue">
              <span className="ip-stat-num">{stats.total}</span>
              <span className="ip-stat-lbl">Total</span>
            </div>
            <div className="ip-stat ip-stat--orange">
              <span className="ip-stat-num">{stats.actifs}</span>
              <span className="ip-stat-lbl">En cours</span>
            </div>
            <div className="ip-stat ip-stat--green">
              <span className="ip-stat-num">{stats.resolus}</span>
              <span className="ip-stat-lbl">Résolus</span>
            </div>
            <div className="ip-stat ip-stat--red">
              <span className="ip-stat-num">{stats.critiques}</span>
              <span className="ip-stat-lbl">Critiques</span>
            </div>
          </div>

          {/* ── FILTRES ── */}
          <div className="ip-filters">
            {FILTERS.map(f => (
              <button
                key={f.key}
                className={`ip-filter-btn${filter === f.key ? ' active' : ''}`}
                onClick={() => setFilter(f.key)}
              >
                {f.label}
                <span className="ip-filter-count">{f.count}</span>
              </button>
            ))}
          </div>

          {/* ── LISTE INCIDENTS ── */}
          <div className="ip-list">
            {filtered.length === 0 ? (
              <div className="ip-empty">
                <CheckCircle2 size={40} color="var(--success)" />
                <p>Aucun incident dans cette catégorie.</p>
              </div>
            ) : filtered.map(inc => {
              const isCrit = inc.criticite === 'critical';
              const isOpen = expanded === inc.id;
              const isRes  = inc.statut === 'resolu';
              const metrics = inc.metriques
                ? (typeof inc.metriques === 'string' ? JSON.parse(inc.metriques) : inc.metriques)
                : null;

              return (
                <div key={inc.id}
                  className={`ip-card ${isRes ? 'ip-card--resolved' : isCrit ? 'ip-card--critical' : 'ip-card--warning'}`}
                >
                  {/* En-tête de la carte */}
                  <div className="ip-card-row" onClick={() => handleExpand(inc.id)}>

                    {/* Titre + antenne */}
                    <div className="ip-card-info">
                      <div className="ip-card-title">{inc.titre}</div>
                      <div className="ip-card-meta">
                        {inc.antenne && <span><strong>{inc.antenne}</strong></span>}
                        {inc.zone    && <span>· {inc.zone}</span>}
                      </div>
                    </div>

                    {/* Badges + heure */}
                    <div className="ip-card-right">
                      <span className={`ip-badge ${isCrit ? 'ip-badge--red' : 'ip-badge--orange'}`}>
                        {isCrit ? 'Critique' : 'Alerte'}
                      </span>
                      <span className={`ip-badge ${isRes ? 'ip-badge--green' : 'ip-badge--gray'}`}>
                        {isRes ? '✓ Résolu' : 'En cours'}
                      </span>
                      <span className="ip-time">
                        <Clock size={12} />
                        {formatDateTimeTN(inc.date_creation)}
                      </span>
                      {isOpen
                        ? <ChevronUp size={16} color="var(--text-light)" />
                        : <ChevronDown size={16} color="var(--text-light)" />
                      }
                    </div>
                  </div>

                  {/* Détails dépliés */}
                  {isOpen && (
                    <div className="ip-detail">

                      {/* Informations générales */}
                      <div className="ip-info-grid">
                        {inc.description && (
                          <div className="ip-info-box">
                            <span className="ip-info-label">Description</span>
                            <span className="ip-info-value">{inc.description}</span>
                          </div>
                        )}
                        {inc.source_detection && (
                          <div className="ip-info-box">
                            <span className="ip-info-label">Source</span>
                            <span className="ip-info-value">{inc.source_detection}</span>
                          </div>
                        )}
                        <div className="ip-info-box">
                          <span className="ip-info-label">Durée depuis détection</span>
                          <span className="ip-info-value">{elapsedStr(inc.date_creation)}</span>
                        </div>
                        {inc.duree_minutes && !isRes && (
                          <div className="ip-info-box">
                            <span className="ip-info-label">Intervention estimée</span>
                            <span className="ip-info-value" style={{ color: isCrit ? 'var(--danger)' : 'var(--warning)', fontWeight: 600 }}>
                              ≈ {inc.duree_minutes} minutes
                            </span>
                          </div>
                        )}
                      </div>

                      {/* Métriques */}
                      {metrics && Object.keys(metrics).length > 0 && (
                        <div className="ip-metrics">
                          <span className="ip-section-label">Métriques au moment de la détection</span>
                          <div className="ip-metrics-list">
                            {Object.entries(metrics).map(([k, v]) => (
                              <div key={k} className="ip-metric-item">
                                <span className="ip-metric-icon">{METRIC_ICONS[k] || <Activity size={12}/>}</span>
                                <span className="ip-metric-key">{k}</span>
                                <span className="ip-metric-val">
                                  {typeof v === 'number' ? v.toFixed(1) : v}
                                  {METRIC_UNITS[k] || ''}
                                </span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Bouton résoudre */}
                      {!isRes && canResolve && (
                        <button
                          className="btn btn-success ip-resolve-btn"
                          onClick={() => handleResolve(inc.id)}
                          disabled={resolving === inc.id}
                        >
                          <CheckCircle2 size={15} />
                          {resolving === inc.id ? 'Résolution en cours…' : 'Marquer comme résolu'}
                        </button>
                      )}

                      {/* Commentaires */}
                      <div className="ip-comments">
                        <span className="ip-section-label">
                          <MessageSquare size={14} color="var(--accent)" /> Commentaires techniques
                        </span>

                        {/* Liste commentaires */}
                        <div className="ip-comment-thread">
                          {comments.length === 0
                            ? <p className="ip-no-comment">Aucun commentaire pour cet incident.</p>
                            : comments.map(c => {
                              const rl = ROLE_LABELS[c.role] || { label: c.role, color: 'var(--text-muted)' };
                              return (
                                <div key={c.id}
                                  className="ip-comment"
                                  style={{ borderLeftColor: c.statut_validation === 'validé' ? 'var(--success)' : 'var(--warning)' }}
                                >
                                  <div className="ip-comment-header">
                                    <span className="ip-comment-author">
                                      <UserCheck size={13} color={rl.color} />
                                      {c.utilisateur_nom}
                                      <span className="ip-role-tag" style={{ color: rl.color, background: rl.color + '15' }}>
                                        {rl.label}
                                      </span>
                                    </span>
                                    <span className="ip-comment-date">
                                      {formatDateTimeTN(c.date_creation)}
                                    </span>
                                  </div>
                                  <p className="ip-comment-text">{c.contenu}</p>
                                  <span className="ip-comment-etat" style={{
                                    color: c.etat_resolution === 'réglé' ? 'var(--success)'
                                         : c.etat_resolution === 'en_cours' ? 'var(--warning)'
                                         : 'var(--text-light)'
                                  }}>
                                    {c.etat_resolution === 'réglé' ? '✔ Réglé'
                                     : c.etat_resolution === 'en_cours' ? '⚙ En cours'
                                     : '⏳ À régler'}
                                  </span>
                                </div>
                              );
                            })
                          }
                        </div>

                        {/* Formulaire nouveau commentaire */}
                        <div className="ip-comment-form">
                          <textarea
                            className="form-input"
                            value={newComment}
                            onChange={e => setNewComment(e.target.value)}
                            placeholder="Ajouter un commentaire technique (ex : antenne redémarrée, câble remplacé…)"
                            rows={3}
                            style={{ resize: 'vertical' }}
                          />
                          <div className="ip-comment-actions">
                            <select
                              className="form-select ip-etat-select"
                              value={newEtat}
                              onChange={e => setNewEtat(e.target.value)}
                            >
                              <option value="à_régler">⏳ À régler</option>
                              <option value="en_cours">⚙ En cours</option>
                              <option value="réglé">✔ Réglé</option>
                            </select>
                            <button
                              className="btn btn-primary"
                              onClick={() => handlePostComment(inc.id)}
                              disabled={!newComment.trim() || sending}
                            >
                              {sending ? 'Envoi…' : 'Envoyer le commentaire'}
                            </button>
                          </div>
                        </div>
                      </div>

                    </div>
                  )}
                </div>
              );
            })}
          </div>

        </div>
      </div>
    </div>
  );
}
