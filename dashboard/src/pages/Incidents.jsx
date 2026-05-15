import React, { useState, useEffect, useCallback } from 'react';
import {
  ShieldCheck, CheckCircle2, Clock, AlertTriangle,
  XCircle, ChevronDown, ChevronUp, RefreshCw, MessageSquare,
  Wrench, UserCheck
} from 'lucide-react';
import axios from 'axios';

import Sidebar from '../components/Sidebar';
import { API_BASE_URL } from '../services/apiConfig';
import { useAuth } from '../auth/AuthContext';
import { DATA_REFRESH_MS } from '../dataRefreshMs';
import '../styles/IncidentsStyles.css';

const CRIT_COLORS = {
  critical: { label: 'Critique', badge: 'badge-danger' },
  warning:  { label: 'Alerte',   badge: 'badge-warning' },
  info:     { label: 'Info',     badge: 'badge-info' },
};

const ROLE_LABELS = {
  administrateur:      { label: 'Administrateur', color: '#7c3aed' },
  ingenieur_reseau:      { label: 'Ingénieur Réseau', color: '#059669' },
  technicien_terrain:  { label: 'Technicien Terrain', color: '#d97706' },
};

export default function ModerationPage() {
  const { token, role } = useAuth();

  const [incidents, setIncidents]         = useState([]);
  const [loading, setLoading]             = useState(true);
  const [expanded, setExpanded]           = useState(null);
  const [filter, setFilter]               = useState('tous');
  const [resolving, setResolving]         = useState(null);
  const [comments, setComments]           = useState([]);
  const [newComment, setNewComment]       = useState('');
  const [newCommentEtat, setNewCommentEtat] = useState('en_cours');
  const [sending, setSending]             = useState(false);

  /* ── current user can resolve ? (admin + mod only) ── */
  const canResolve = ['administrateur', 'ingenieur_reseau'].includes(role);

  const fetchIncidents = useCallback(async () => {
    if (!token) return;
    try {
      const res = await axios.get(`${API_BASE_URL}/incidents`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setIncidents(res.data);
    } catch (_) {}
    finally { setLoading(false); }
  }, [token]);

  useEffect(() => {
    fetchIncidents();
    const id = setInterval(fetchIncidents, DATA_REFRESH_MS);
    return () => clearInterval(id);
  }, [fetchIncidents]);

  const handleResolve = async (id) => {
    setResolving(id);
    try {
      await axios.put(
        `${API_BASE_URL}/incidents/${id}/resolve`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      await fetchIncidents();
    } catch (_) {}
    setResolving(null);
  };

  const loadComments = async (incId) => {
    try {
      const res = await axios.get(`${API_BASE_URL}/incidents/${incId}/commentaires`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setComments(res.data);
    } catch (_) {}
  };

  const handleExpand = (id) => {
    if (expanded === id) {
      setExpanded(null);
    } else {
      setExpanded(id);
      setComments([]);
      loadComments(id);
    }
  };

  const handlePostComment = async (incId) => {
    if (!newComment.trim()) return;
    setSending(true);
    try {
      await axios.post(
        `${API_BASE_URL}/incidents/${incId}/commentaires`,
        { contenu: newComment, etat_resolution: newCommentEtat },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setNewComment('');
      setNewCommentEtat('en_cours');
      await loadComments(incId);
      if (newCommentEtat === 'réglé') await fetchIncidents();
    } catch (e) {
      const msg = e.response?.data?.error || "Erreur lors de l'envoi du commentaire.";
      alert(msg);
    } finally {
      setSending(false);
    }
  };

  const FILTERS = [
    { key: 'tous',     label: 'Tous',      count: incidents.length },
    { key: 'en_cours', label: 'En cours',  count: incidents.filter(i => i.statut === 'en_cours').length },
    { key: 'resolu',   label: 'Résolus',   count: incidents.filter(i => i.statut === 'resolu').length },
    { key: 'critical', label: 'Critiques', count: incidents.filter(i => i.criticite === 'critical').length },
  ];

  const filtered = incidents.filter(inc => {
    if (filter === 'tous')     return true;
    if (filter === 'critical') return inc.criticite === 'critical';
    return inc.statut === filter;
  });

  const stats = {
    actifs:    incidents.filter(i => i.statut === 'en_cours').length,
    resolus:   incidents.filter(i => i.statut === 'resolu').length,
    critiques: incidents.filter(i => i.criticite === 'critical').length,
  };

  /* ── page title / subtitle per role ── */
  const pageTitle = role === 'technicien_terrain'
    ? 'Interventions Terrain'
    : 'Gestion des Incidents';
  const pageSubtitle = role === 'technicien_terrain'
    ? 'Anomalies et alertes détectées par l\'IA — ajoutez vos commentaires techniques'
    : 'Validation et résolution des anomalies réseau détectées par Isolation Forest';

  if (loading) return (
    <div style={{ display: 'flex' }}>
      <Sidebar />
      <div className="loading-center" style={{ flex: 1 }}><div className="spinner" /></div>
    </div>
  );

  return (
    <div style={{ display: 'flex' }}>
      <Sidebar />
      <div className="page-content">
        <div className="page-shell">

          {/* ── HEADER ── */}
          <div className="page-header">
            <div className="page-header-left">
              <h1>
                {role === 'technicien_terrain'
                  ? <Wrench size={22} color="var(--accent)" />
                  : <ShieldCheck size={22} color="var(--accent)" />
                }
                {' '}{pageTitle}
              </h1>
              <p>{pageSubtitle}</p>
            </div>
            <button className="btn btn-secondary" onClick={fetchIncidents}>
              <RefreshCw size={14} /> Actualiser
            </button>
          </div>

          {/* ── KPI STATS ── */}
          <div style={{ display: 'flex', gap: 16, marginBottom: 8 }}>
            {[
              { label: 'En cours',  value: stats.actifs,    color: 'var(--warning)', icon: <AlertTriangle size={18} /> },
              { label: 'Résolus',   value: stats.resolus,   color: 'var(--success)', icon: <CheckCircle2 size={18} /> },
              { label: 'Critiques', value: stats.critiques, color: 'var(--danger)',  icon: <XCircle size={18} /> },
            ].map(s => (
              <div key={s.label} className="kpi-card" style={{ flex: 1 }}>
                <div className="kpi-icon" style={{ background: `${s.color}18`, color: s.color }}>{s.icon}</div>
                <div className="kpi-body">
                  <div className="kpi-label">{s.label}</div>
                  <div className="kpi-value" style={{ color: s.color }}>{s.value}</div>
                </div>
              </div>
            ))}
          </div>

          {/* ── FILTER TABS ── */}
          <div className="mod-filter-tabs">
            {FILTERS.map(f => (
              <button
                key={f.key}
                className={`mod-tab${filter === f.key ? ' active' : ''}`}
                onClick={() => setFilter(f.key)}
              >
                {f.label} <span className="mod-tab-count">{f.count}</span>
              </button>
            ))}
          </div>

          {/* ── INCIDENTS LIST ── */}
          <div className="panel" style={{ padding: 0, overflow: 'hidden' }}>
            {filtered.length === 0 ? (
              <div className="empty-state" style={{ padding: '60px 20px' }}>
                <CheckCircle2 size={36} color="var(--success)" />
                <p>Aucun incident dans cette catégorie.</p>
              </div>
            ) : filtered.map(inc => {
              const crit       = CRIT_COLORS[inc.criticite] || CRIT_COLORS.info;
              const isOpen     = expanded === inc.id;
              const isResolved = inc.statut === 'resolu';

              return (
                <div key={inc.id} className={`mod-incident${isResolved ? ' resolved' : ''}`}>

                  {/* ── Row header ── */}
                  <div className="mod-incident-row" onClick={() => handleExpand(inc.id)}>
                    <div className={`mod-incident-bar ${inc.criticite}`} />
                    <div className="mod-incident-info">
                      <span className="mod-incident-title">{inc.titre}</span>
                      <span className="mod-incident-meta">{inc.antenne} · {inc.zone}</span>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexShrink: 0 }}>
                      <span className={`badge ${crit.badge}`}>{crit.label}</span>
                      <span className={`badge ${isResolved ? 'badge-success' : 'badge-warning'}`}>
                        {isResolved ? 'Résolu' : 'En cours'}
                      </span>
                      <span style={{ color: 'var(--text-muted)', fontSize: '0.78rem', display: 'flex', alignItems: 'center', gap: 4 }}>
                        <Clock size={12} />
                        {new Date(inc.date_creation).toLocaleString('fr-FR', { dateStyle: 'short', timeStyle: 'short' })}
                      </span>
                      {isOpen ? <ChevronUp size={16} color="var(--text-muted)" /> : <ChevronDown size={16} color="var(--text-muted)" />}
                    </div>
                  </div>

                  {/* ── Expanded details ── */}
                  {isOpen && (
                    <div className="mod-incident-detail">
                      <div className="mod-detail-grid">
                        <div className="mod-detail-item">
                          <label>Description</label>
                          <p>{inc.description || 'Aucune description disponible.'}</p>
                        </div>
                        <div className="mod-detail-item">
                          <label>Source de détection</label>
                          <p>{inc.source_detection || 'Isolation Forest'}</p>
                        </div>
                        {inc.duree_minutes && (
                          <div className="mod-detail-item">
                            <label>Durée estimée</label>
                            <p>{inc.duree_minutes} minutes</p>
                          </div>
                        )}
                        {inc.metriques && (
                          <div className="mod-detail-item" style={{ gridColumn: '1 / -1' }}>
                            <label>Métriques au moment de la détection</label>
                            <div className="mod-metrics-row">
                              {Object.entries(
                                typeof inc.metriques === 'string' ? JSON.parse(inc.metriques) : inc.metriques
                              ).map(([k, v]) => (
                                <div key={k} className="mod-metric-chip">
                                  <span>{k}</span>
                                  <strong>{typeof v === 'number' ? v.toFixed(1) : v}</strong>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>

                      {/* Bouton résoudre — admin + modérateur seulement */}
                      {!isResolved && canResolve && (
                        <div style={{ marginTop: 16, display: 'flex', gap: 10 }}>
                          <button
                            className="btn btn-primary"
                            onClick={() => handleResolve(inc.id)}
                            disabled={resolving === inc.id}
                          >
                            <CheckCircle2 size={15} />
                            {resolving === inc.id ? 'Résolution…' : 'Marquer comme résolu'}
                          </button>
                        </div>
                      )}

                      {/* ── Commentaires techniques ── */}
                      <div className="mod-comments-section" style={{ marginTop: 24, borderTop: '1px solid var(--border)', paddingTop: 16 }}>
                        <h4 style={{ marginBottom: 12, fontSize: '1rem', color: 'var(--text)', display: 'flex', alignItems: 'center', gap: 8 }}>
                          <MessageSquare size={16} color="var(--accent)" /> Commentaires techniques
                        </h4>

                        {/* Thread */}
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 12, marginBottom: 16, maxHeight: 280, overflowY: 'auto' }}>
                          {comments.length === 0 ? (
                            <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', fontStyle: 'italic' }}>
                              Aucun commentaire pour cet incident.
                            </p>
                          ) : comments.map(c => {
                            const rl = ROLE_LABELS[c.role] || { label: c.role, color: 'var(--text-muted)' };
                            return (
                              <div key={c.id} style={{
                                background: 'var(--surface-hover)',
                                padding: '12px 14px',
                                borderRadius: 'var(--radius-sm)',
                                borderLeft: `3px solid ${c.statut_validation === 'validé' ? 'var(--success)' : 'var(--warning)'}`
                              }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                                  <span style={{ fontWeight: 600, fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: 6 }}>
                                    <UserCheck size={13} color={rl.color} />
                                    {c.utilisateur_nom}
                                    <span style={{ background: rl.color + '22', color: rl.color, fontSize: '0.7rem', padding: '1px 7px', borderRadius: 20, fontWeight: 600 }}>
                                      {rl.label}
                                    </span>
                                  </span>
                                  <span style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>{c.date_creation?.substring(0, 16)?.replace('T', ' ')}</span>
                                </div>
                                <p style={{ margin: '6px 0 8px', fontSize: '0.9rem', lineHeight: 1.5 }}>{c.contenu}</p>
                                <div style={{ display: 'flex', gap: 12, alignItems: 'center', flexWrap: 'wrap' }}>
                                  {c.statut_validation === 'validé' ? (
                                    <span style={{ fontSize: '0.74rem', color: 'var(--success)', display: 'flex', alignItems: 'center', gap: 3 }}>
                                      <CheckCircle2 size={11} /> Validé par administrateur
                                    </span>
                                  ) : (
                                    <span style={{ fontSize: '0.74rem', color: 'var(--warning)', display: 'flex', alignItems: 'center', gap: 3 }}>
                                      <Clock size={11} /> En attente de validation
                                    </span>
                                  )}
                                  <span style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>
                                    État : <strong style={{ color: c.etat_resolution === 'réglé' ? 'var(--success)' : c.etat_resolution === 'en_cours' ? 'var(--warning)' : 'var(--text-muted)' }}>
                                      {c.etat_resolution === 'réglé' ? '✔ Réglé' : c.etat_resolution === 'en_cours' ? '⚙ En cours' : '⏳ À régler'}
                                    </strong>
                                  </span>
                                </div>
                              </div>
                            );
                          })}
                        </div>

                        {/* Formulaire nouveau commentaire */}
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                          <textarea
                            value={newComment}
                            onChange={e => setNewComment(e.target.value)}
                            placeholder="Ajouter un commentaire technique (ex: Antenne redémarrée, surchauffe confirmée…)"
                            className="admin-input"
                            style={{ minHeight: 64, resize: 'vertical' }}
                          />
                          <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
                            <select
                              className="admin-input"
                              value={newCommentEtat}
                              onChange={e => setNewCommentEtat(e.target.value)}
                              style={{ width: 160 }}
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
