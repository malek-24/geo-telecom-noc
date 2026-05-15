/**
 * EquipmentsPage.js — Gestion des antennes avec CRUD
 * Rôles autorisés pour les actions :
 *   - Ajouter / Modifier : administrateur, ingenieur_reseau
 *   - Supprimer          : administrateur uniquement
 *   - Consulter          : tous les rôles
 */
import React, { useState, useEffect, useCallback } from 'react';
import {
  RadioTower, Search, Filter, Plus, Edit2, Trash2,
  X, CheckCircle2, AlertTriangle, Activity, MapPin, Save, Loader
} from 'lucide-react';
import axios from 'axios';
import Sidebar from '../components/Sidebar';
import { API_BASE_URL } from '../services/apiConfig';
import { useAuth } from '../auth/AuthContext';
import { DATA_REFRESH_MS } from '../dataRefreshMs';
import '../styles/EquipmentsStyles.css';

// Zones disponibles à Mahdia
const ZONES_MAHDIA = [
  'Mahdia Centre', 'Mahdia Nord', 'Mahdia Sud', 'Mahdia Est', 'Mahdia Ouest',
  'Ksour Essef', 'El Jem', 'Chebba', 'Salakta', 'Melloulèche',
  'Sidi Alouane', 'Bou Merdes', 'Ouled Chamekh', 'Hebira'
];

const TYPES_ANTENNE = ['4G LTE', '4G+', '5G', '3G', 'Micro', 'Macro'];

const STATUS_BADGE = {
  normal:     { label: 'Normal',     cls: 'badge-success' },
  alerte:     { label: 'Alerte',     cls: 'badge-warning' },
  critique:   { label: 'Critique',   cls: 'badge-danger'  },
  maintenance:{ label: 'Maintenance',cls: 'badge-info'    },
  en_attente: { label: 'En attente', cls: 'badge-info'    },
};

const VIDE_FORM = {
  nom: '', zone: ZONES_MAHDIA[0], type: TYPES_ANTENNE[0],
  latitude: '', longitude: '', operateur: 'Tunisie Telecom', statut: 'normal'
};

export default function EquipmentsPage() {
  const { token, role } = useAuth();
  const [antennes, setAntennes] = useState([]);
  const [loading, setLoading]   = useState(true);
  const [search, setSearch]     = useState('');
  const [filterZone, setFilterZone]     = useState('');
  const [filterStatut, setFilterStatut] = useState('');
  const [sortKey, setSortKey]   = useState('statut');
  const [sortDir, setSortDir]   = useState('asc');

  // Modal CRUD
  const [modalOuvert, setModalOuvert] = useState(false);
  const [modEdition, setModEdition]   = useState(null); // null = création, objet = édition
  const [form, setForm]               = useState(VIDE_FORM);
  const [saving, setSaving]           = useState(false);
  const [errForm, setErrForm]         = useState('');

  // Confirmation suppression
  const [confirmSuppr, setConfirmSuppr] = useState(null);

  const peutEditer    = ['administrateur', 'ingenieur_reseau'].includes(role);
  const peutSupprimer = role === 'administrateur';

  // ── Récupération des antennes ───────────────────────────────
  const fetchAntennes = useCallback(async () => {
    if (!token) return;
    try {
      const res = await axios.get(`${API_BASE_URL}/antennes`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setAntennes(res.data);
    } catch (_) {}
    finally { setLoading(false); }
  }, [token]);

  useEffect(() => {
    fetchAntennes();
    const id = setInterval(fetchAntennes, DATA_REFRESH_MS);
    return () => clearInterval(id);
  }, [fetchAntennes]);

  // ── Filtrage + tri ──────────────────────────────────────────
  const STATUS_ORDER = { critique: 0, alerte: 1, maintenance: 2, normal: 3, en_attente: 4 };

  const antFiltrees = antennes
    .filter(a => {
      const ok1 = !search || a.nom?.toLowerCase().includes(search.toLowerCase()) || a.zone?.toLowerCase().includes(search.toLowerCase());
      const ok2 = !filterZone   || a.zone   === filterZone;
      const ok3 = !filterStatut || a.statut === filterStatut;
      return ok1 && ok2 && ok3;
    })
    .sort((a, b) => {
      let va, vb;
      if (sortKey === 'statut')     { va = STATUS_ORDER[a.statut] ?? 9; vb = STATUS_ORDER[b.statut] ?? 9; }
      else if (sortKey === 'nom')   { va = (a.nom   || '').toLowerCase(); vb = (b.nom   || '').toLowerCase(); }
      else if (sortKey === 'zone')  { va = (a.zone  || '').toLowerCase(); vb = (b.zone  || '').toLowerCase(); }
      else if (sortKey === 'score') { va = Number(a.risk_score  || 0); vb = Number(b.risk_score  || 0); }
      else if (sortKey === 'temp')  { va = Number(a.temperature || 0); vb = Number(b.temperature || 0); }
      else { va = 0; vb = 0; }
      if (va < vb) return sortDir === 'asc' ? -1 : 1;
      if (va > vb) return sortDir === 'asc' ?  1 : -1;
      return 0;
    });

  const toggleSort = (key) => {
    if (sortKey === key) setSortDir(d => d === 'asc' ? 'desc' : 'asc');
    else { setSortKey(key); setSortDir('asc'); }
  };

  const sortIcon = (key) => sortKey === key ? (sortDir === 'asc' ? ' ↑' : ' ↓') : ' ⇅';

  const zones   = [...new Set(antennes.map(a => a.zone).filter(Boolean))].sort();
  const statuts = ['normal', 'alerte', 'critique', 'maintenance'];

  // ── Modal helpers ───────────────────────────────────────────
  const ouvrirCreation = () => {
    setModEdition(null);
    setForm(VIDE_FORM);
    setErrForm('');
    setModalOuvert(true);
  };

  const ouvrirEdition = (ant) => {
    setModEdition(ant);
    setForm({
      nom: ant.nom || '', zone: ant.zone || ZONES_MAHDIA[0], type: ant.type || TYPES_ANTENNE[0],
      latitude: ant.latitude || '', longitude: ant.longitude || '',
      operateur: ant.operateur || 'Tunisie Telecom',
      statut: ant.statut || 'normal'
    });
    setErrForm('');
    setModalOuvert(true);
  };

  const fermerModal = () => {
    setModalOuvert(false);
    setModEdition(null);
    setErrForm('');
  };

  // ── Validation formulaire ───────────────────────────────────
  const validerForm = () => {
    if (!form.nom.trim()) return 'Le nom de l\'antenne est requis.';
    if (!form.zone)       return 'Veuillez sélectionner une zone.';
    if (!form.latitude || isNaN(parseFloat(form.latitude))) return 'Latitude invalide.';
    if (!form.longitude || isNaN(parseFloat(form.longitude))) return 'Longitude invalide.';
    const lat = parseFloat(form.latitude);
    const lng = parseFloat(form.longitude);
    if (lat < 33 || lat > 38) return 'Latitude hors Tunisie (33°–38°N).';
    if (lng < 8  || lng > 12) return 'Longitude hors Tunisie (8°–12°E).';
    return null;
  };

  // ── Créer ou modifier ───────────────────────────────────────
  const sauvegarder = async (e) => {
    e.preventDefault();
    const erreur = validerForm();
    if (erreur) { setErrForm(erreur); return; }

    setSaving(true); setErrForm('');
    try {
      const headers = { Authorization: `Bearer ${token}` };
      const payload = { ...form, latitude: parseFloat(form.latitude), longitude: parseFloat(form.longitude) };

      if (modEdition) {
        await axios.put(`${API_BASE_URL}/antennes/${modEdition.id}`, payload, { headers });
      } else {
        await axios.post(`${API_BASE_URL}/antennes`, payload, { headers });
      }
      fermerModal();
      fetchAntennes();
    } catch (err) {
      setErrForm(err.response?.data?.error || 'Erreur lors de la sauvegarde.');
    } finally {
      setSaving(false);
    }
  };

  // ── Supprimer ────────────────────────────────────────────────
  const supprimer = async (ant) => {
    try {
      await axios.delete(`${API_BASE_URL}/antennes/${ant.id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setConfirmSuppr(null);
      fetchAntennes();
    } catch (err) {
      alert(err.response?.data?.error || 'Erreur lors de la suppression.');
    }
  };

  // ── Compteurs ───────────────────────────────────────────────
  const nb = {
    total:    antennes.length,
    normal:   antennes.filter(a => a.statut === 'normal').length,
    alerte:   antennes.filter(a => a.statut === 'alerte').length,
    critique: antennes.filter(a => a.statut === 'critique').length,
  };

  if (loading) return (
    <div style={{ display: 'flex' }}>
      <Sidebar />
      <div className="loading-center" style={{ flex: 1 }}>
        <div className="spinner" />
        <p>Chargement des antennes…</p>
      </div>
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
              <h1><RadioTower size={22} color="var(--accent)" /> Gestion des Antennes</h1>
              <p>Inventaire complet • {nb.total} sites supervisés</p>
            </div>
            {peutEditer && (
              <button className="btn btn-primary" onClick={ouvrirCreation}>
                <Plus size={16} /> Ajouter une antenne
              </button>
            )}
          </div>

          {/* ── KPIs ── */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16, marginBottom: 24 }}>
            {[
              { label: 'Total sites',   value: nb.total,    color: 'var(--accent)',   icon: <RadioTower size={18} /> },
              { label: 'Sites normaux', value: nb.normal,   color: 'var(--success)',  icon: <CheckCircle2 size={18} /> },
              { label: 'En alerte',     value: nb.alerte,   color: 'var(--warning)',  icon: <AlertTriangle size={18} /> },
              { label: 'Critiques',     value: nb.critique, color: 'var(--danger)',   icon: <Activity size={18} /> },
            ].map(k => (
              <div key={k.label} className="kpi-card" style={{ borderTop: `3px solid ${k.color}` }}>
                <div className="kpi-icon" style={{ color: k.color }}>{k.icon}</div>
                <div className="kpi-body">
                  <div className="kpi-label">{k.label}</div>
                  <div className="kpi-value" style={{ color: k.color, fontSize: '1.5rem' }}>{k.value}</div>
                </div>
              </div>
            ))}
          </div>

          {/* ── FILTRES ── */}
          <div className="panel" style={{ marginBottom: 20 }}>
            <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'center' }}>
              <div style={{ position: 'relative', flex: 1, minWidth: 220 }}>
                <Search size={14} style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
                <input
                  className="form-input"
                  style={{ paddingLeft: 32 }}
                  placeholder="Rechercher nom ou zone…"
                  value={search}
                  onChange={e => setSearch(e.target.value)}
                />
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <Filter size={14} color="var(--text-muted)" />
                <select className="form-input" value={filterZone} onChange={e => setFilterZone(e.target.value)} style={{ minWidth: 160 }}>
                  <option value="">Toutes les zones</option>
                  {zones.map(z => <option key={z} value={z}>{z}</option>)}
                </select>
              </div>
              <select className="form-input" value={filterStatut} onChange={e => setFilterStatut(e.target.value)} style={{ minWidth: 150 }}>
                <option value="">Tous les statuts</option>
                {statuts.map(s => <option key={s} value={s}>{s.charAt(0).toUpperCase() + s.slice(1)}</option>)}
              </select>
              {/* ── Sort buttons ── */}
              <div style={{ display: 'flex', gap: 5, flexWrap: 'wrap' }}>
                {[
                  { k: 'statut', l: 'Statut (auto)' },
                  { k: 'nom',    l: 'Nom' },
                  { k: 'zone',   l: 'Zone' },
                  { k: 'score',  l: 'Score IA' },
                  { k: 'temp',   l: 'Temp.' },
                ].map(({ k, l }) => (
                  <button
                    key={k}
                    onClick={() => toggleSort(k)}
                    style={{
                      padding: '5px 10px', borderRadius: 6,
                      border: sortKey === k ? '1.5px solid var(--accent)' : '1px solid var(--border)',
                      background: sortKey === k ? 'var(--accent-soft)' : 'var(--surface)',
                      color: sortKey === k ? 'var(--accent)' : 'var(--text-muted)',
                      fontSize: '0.74rem', fontWeight: 600, cursor: 'pointer', fontFamily: 'inherit',
                      transition: 'all 0.15s',
                    }}
                  >
                    {l}{sortIcon(k)}
                  </button>
                ))}
              </div>
              <span style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginLeft: 'auto' }}>
                {antFiltrees.length} / {antennes.length} sites
              </span>
            </div>
          </div>


          {/* ── TABLEAU ── */}
          <div className="panel">
            <div style={{ overflowX: 'auto' }}>
              <table className="noc-table">
                <thead>
                  <tr>
                    <th>Site</th>
                    <th>Zone</th>
                    <th>Type</th>
                    <th>CPU (%)</th>
                    <th>Temp (°C)</th>
                    <th>Dispo (%)</th>
                    <th>Latence (ms)</th>
                    <th>Score IA</th>
                    <th>Statut</th>
                    <th>Coordonnées</th>
                    {peutEditer && <th>Actions</th>}
                  </tr>
                </thead>
                <tbody>
                  {antFiltrees.slice(0, 60).map(ant => {
                    const badge = STATUS_BADGE[ant.statut] || STATUS_BADGE.en_attente;
                    return (
                      <tr key={ant.id}>
                        <td style={{ fontWeight: 600 }}>{ant.nom}</td>
                        <td style={{ color: 'var(--text-muted)' }}>{ant.zone}</td>
                        <td><span className="badge badge-info">{ant.type}</span></td>
                        <td style={{ color: ant.cpu > 85 ? 'var(--danger)' : 'inherit', fontWeight: ant.cpu > 85 ? 700 : 400 }}>
                          {Number(ant.cpu || 0).toFixed(1)}
                        </td>
                        <td style={{ color: ant.temperature > 80 ? 'var(--danger)' : 'inherit' }}>
                          {Number(ant.temperature || 0).toFixed(1)}
                        </td>
                        <td style={{ color: ant.disponibilite < 95 ? 'var(--danger)' : 'var(--success)', fontWeight: 600 }}>
                          {Number(ant.disponibilite || 0).toFixed(1)}
                        </td>
                        <td style={{ color: ant.latence > 60 ? 'var(--warning)' : 'inherit' }}>
                          {Number(ant.latence || 0).toFixed(0)}
                        </td>
                        <td style={{ fontWeight: 700, color: 'var(--accent)' }}>
                          {Number(ant.risk_score || 0).toFixed(1)}%
                        </td>
                        <td>
                          <span className={`badge ${badge.cls}`}>{badge.label}</span>
                        </td>
                        <td style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                          <MapPin size={11} style={{ marginRight: 3 }} />
                          {Number(ant.latitude).toFixed(4)}, {Number(ant.longitude).toFixed(4)}
                        </td>
                        {peutEditer && (
                          <td>
                            <div style={{ display: 'flex', gap: 6 }}>
                              <button
                                className="btn btn-sm"
                                title="Modifier"
                                onClick={() => ouvrirEdition(ant)}
                                style={{ padding: '4px 8px', background: 'var(--accent-soft)', color: 'var(--accent)', border: '1px solid rgba(37,99,235,0.2)' }}
                              >
                                <Edit2 size={13} />
                              </button>
                              {peutSupprimer && (
                                <button
                                  className="btn btn-sm"
                                  title="Supprimer"
                                  onClick={() => setConfirmSuppr(ant)}
                                  style={{ padding: '4px 8px', background: 'var(--danger-bg)', color: 'var(--danger)', border: '1px solid rgba(220,38,38,0.2)' }}
                                >
                                  <Trash2 size={13} />
                                </button>
                              )}
                            </div>
                          </td>
                        )}
                      </tr>
                    );
                  })}
                </tbody>
              </table>
              {antFiltrees.length === 0 && (
                <div className="empty-state" style={{ padding: 40 }}>
                  <RadioTower size={32} color="var(--text-muted)" />
                  <p>Aucune antenne trouvée pour ces critères.</p>
                </div>
              )}
            </div>
          </div>

        </div>
      </div>

      {/* ── MODAL CRUD ── */}
      {modalOuvert && (
        <>
          <div onClick={fermerModal} style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', zIndex: 1000 }} />
          <div style={{
            position: 'fixed', top: '50%', left: '50%',
            transform: 'translate(-50%, -50%)',
            zIndex: 1001, width: 480, maxWidth: '95vw',
            background: 'var(--surface)', borderRadius: 18,
            border: '1px solid var(--border)',
            boxShadow: '0 20px 60px rgba(0,0,0,0.5)',
            overflow: 'hidden',
            animation: 'fadeIn 0.2s ease'
          }}>
            {/* Header modal */}
            <div style={{ padding: '20px 24px 16px', borderBottom: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <h3 style={{ margin: 0, fontSize: '1.05rem', fontWeight: 700 }}>
                  <RadioTower size={16} color="var(--accent)" style={{ marginRight: 8 }} />
                  {modEdition ? `Modifier — ${modEdition.nom}` : 'Ajouter une antenne'}
                </h3>
                <p style={{ margin: '4px 0 0', fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                  {modEdition ? 'Modifiez les informations de cette antenne.' : 'Remplissez les informations du nouveau site.'}
                </p>
              </div>
              <button onClick={fermerModal} style={{ background: 'var(--surface-2)', border: 'none', borderRadius: 8, padding: 6, cursor: 'pointer', color: 'var(--text-muted)', display: 'flex' }}>
                <X size={16} />
              </button>
            </div>

            {/* Corps du formulaire */}
            <form onSubmit={sauvegarder}>
              <div style={{ padding: '20px 24px', display: 'flex', flexDirection: 'column', gap: 14 }}>

                {errForm && (
                  <div style={{ background: 'var(--danger-bg)', color: 'var(--danger)', padding: '10px 14px', borderRadius: 8, fontSize: '0.82rem', border: '1px solid rgba(220,38,38,0.2)' }}>
                    {errForm}
                  </div>
                )}

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
                  <div>
                    <label className="form-label">Nom du site *</label>
                    <input className="form-input" placeholder="ex: TT-121" value={form.nom} onChange={e => setForm(f => ({ ...f, nom: e.target.value }))} required />
                  </div>
                  <div>
                    <label className="form-label">Type d'antenne *</label>
                    <select className="form-input" value={form.type} onChange={e => setForm(f => ({ ...f, type: e.target.value }))}>
                      {TYPES_ANTENNE.map(t => <option key={t} value={t}>{t}</option>)}
                    </select>
                  </div>
                </div>

                <div>
                  <label className="form-label">Zone géographique *</label>
                  <select className="form-input" value={form.zone} onChange={e => setForm(f => ({ ...f, zone: e.target.value }))}>
                    {ZONES_MAHDIA.map(z => <option key={z} value={z}>{z}</option>)}
                  </select>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
                  <div>
                    <label className="form-label">Latitude *</label>
                    <input className="form-input" type="number" step="0.0001" placeholder="35.xxxx" value={form.latitude} onChange={e => setForm(f => ({ ...f, latitude: e.target.value }))} required />
                  </div>
                  <div>
                    <label className="form-label">Longitude *</label>
                    <input className="form-input" type="number" step="0.0001" placeholder="10.xxxx" value={form.longitude} onChange={e => setForm(f => ({ ...f, longitude: e.target.value }))} required />
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
                  <div>
                    <label className="form-label">Opérateur</label>
                    <input className="form-input" value={form.operateur} onChange={e => setForm(f => ({ ...f, operateur: e.target.value }))} />
                  </div>
                  <div>
                    <label className="form-label">Statut</label>
                    <select className="form-input" value={form.statut || 'normal'} onChange={e => setForm(f => ({ ...f, statut: e.target.value }))}>
                      <option value="normal">Normal</option>
                      <option value="alerte">Alerte</option>
                      <option value="critique">Critique</option>
                      <option value="maintenance">En Maintenance</option>
                    </select>
                  </div>
                </div>

              </div>

              {/* Footer modal */}
              <div style={{ padding: '16px 24px', borderTop: '1px solid var(--border)', display: 'flex', gap: 10, justifyContent: 'flex-end' }}>
                <button type="button" onClick={fermerModal} className="btn" style={{ background: 'var(--surface-2)', color: 'var(--text-muted)', border: '1px solid var(--border)' }}>
                  Annuler
                </button>
                <button type="submit" className="btn btn-primary" disabled={saving}>
                  {saving ? <><Loader size={14} className="spin" /> Sauvegarde…</> : <><Save size={14} /> {modEdition ? 'Enregistrer' : 'Créer l\'antenne'}</>}
                </button>
              </div>
            </form>
          </div>
        </>
      )}

      {/* ── CONFIRMATION SUPPRESSION ── */}
      {confirmSuppr && (
        <>
          <div onClick={() => setConfirmSuppr(null)} style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', zIndex: 1000 }} />
          <div style={{
            position: 'fixed', top: '50%', left: '50%',
            transform: 'translate(-50%, -50%)',
            zIndex: 1001, width: 380, maxWidth: '90vw',
            background: 'var(--surface)', borderRadius: 16,
            border: '1px solid var(--border)',
            boxShadow: '0 16px 50px rgba(0,0,0,0.5)',
            padding: '28px 28px 24px',
            textAlign: 'center'
          }}>
            <div style={{ width: 52, height: 52, background: 'var(--danger-bg)', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 16px' }}>
              <Trash2 size={22} color="var(--danger)" />
            </div>
            <h3 style={{ margin: '0 0 8px', fontSize: '1rem', fontWeight: 700 }}>Supprimer {confirmSuppr.nom} ?</h3>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', margin: '0 0 24px' }}>
              Cette action supprimera définitivement l'antenne, ses mesures et ses incidents associés. Irréversible.
            </p>
            <div style={{ display: 'flex', gap: 10, justifyContent: 'center' }}>
              <button onClick={() => setConfirmSuppr(null)} className="btn" style={{ background: 'var(--surface-2)', color: 'var(--text-muted)', border: '1px solid var(--border)' }}>
                Annuler
              </button>
              <button onClick={() => supprimer(confirmSuppr)} className="btn" style={{ background: 'var(--danger)', color: '#fff', border: 'none' }}>
                <Trash2 size={14} /> Supprimer définitivement
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
