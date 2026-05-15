import React, { useState, useEffect, useCallback } from 'react';
import {
  Activity, Wifi, AlertTriangle, Clock,
  RadioTower, CheckCircle2, ShieldAlert, BrainCircuit, Map
} from 'lucide-react';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer
} from 'recharts';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

import Sidebar from '../components/Sidebar';
import { API_BASE_URL } from '../services/apiConfig';
import { useAuth } from '../auth/AuthContext';
import { DATA_REFRESH_MS } from '../dataRefreshMs';
import '../styles/DashboardStyles.css';


// ── KPI Card ─────────────────────────────────────────────────
function KPICard({ title, value, subtitle, icon, iconBg, valueColor }) {
  return (
    <div className="kpi-card">
      <div className="kpi-icon" style={{ background: iconBg || 'var(--accent-soft)' }}>
        {icon}
      </div>
      <div className="kpi-body">
        <div className="kpi-label">{title}</div>
        <div className="kpi-value" style={{ color: valueColor || 'var(--text)' }}>{value}</div>
        {subtitle && <div className="kpi-sub">{subtitle}</div>}
      </div>
    </div>
  );
}

// ── Chart Tooltip ─────────────────────────────────────────────
const ChartTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 'var(--radius-sm)', padding: '10px 14px', fontSize: '0.8rem' }}>
      <p style={{ fontWeight: 600, color: 'var(--text-muted)', marginBottom: 4 }}>{label}</p>
      {payload.map(p => (
        <p key={p.dataKey} style={{ color: p.color }}>
          {p.name}: <strong>{p.value}</strong>
        </p>
      ))}
    </div>
  );
};

export default function Dashboard() {
  const { token } = useAuth();
  const navigate = useNavigate();

  const [summary, setSummary]       = useState(null);
  const [incidents, setIncidents]   = useState([]);
  const [history, setHistory]       = useState([]);
  // Data fetch
  const fetchAll = useCallback(async () => {
    if (!token) return;
    const cfg = { headers: { Authorization: `Bearer ${token}` } };
    try {
      const [sRes, aRes, iRes, hRes] = await Promise.all([
        axios.get(`${API_BASE_URL}/dashboard/summary`, cfg),
        axios.get(`${API_BASE_URL}/antennes`, cfg),
        axios.get(`${API_BASE_URL}/incidents`, cfg),
        axios.get(`${API_BASE_URL}/dashboard/history`, cfg),
      ]);
      setSummary(sRes.data);
      setIncidents(iRes.data.filter(i => i.statut !== 'resolu'));
      setHistory(hRes.data);
    } catch (e) { /* silent fail on poll */ }
  }, [token]);

  useEffect(() => {
    fetchAll();
    const interval = setInterval(fetchAll, DATA_REFRESH_MS);
    return () => clearInterval(interval);
  }, [fetchAll]);

  const s = summary;

  return (
    <div style={{ display: 'flex' }}>
      <Sidebar />
      <div className="page-content">
        <div className="dashboard-container">

          {/* ── HEADER ── */}
          <div className="dashboard-header">
            <div>
              <h1><Wifi size={22} color="var(--accent)" /> Tableau de Bord NOC</h1>
              <p>Supervision temps réel — Mahdia, Tunisie</p>
            </div>
            <div className="header-right" style={{ display: 'flex', gap: 10 }}>
              <button 
                className="btn btn-secondary" 
                onClick={async () => {
                  try {
                    await axios.post(`${API_BASE_URL}/api/test-ia`, { type: 'surchauffe' }, { headers: { Authorization: `Bearer ${token}` } });
                    fetchAll();
                  } catch (e) { alert("Erreur simulation IA"); }
                }}
                style={{ background: 'var(--danger-bg)', color: 'var(--danger)', border: 'none', padding: '6px 12px', fontSize: '0.9rem', borderRadius: '4px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 6 }}
              >
                <AlertTriangle size={14} /> Simuler Anomalie IA
              </button>
              <div className="system-status-chip">
                <CheckCircle2 size={14} /> Réseau Opérationnel
              </div>
            </div>
          </div>

          {/* ── KPIs ── */}
          <div className="dashboard-kpi-grid">
            <KPICard
              title="Sites Normaux"
              value={s?.en_ligne ?? '—'}
              subtitle={`sur ${s?.total_antennes ?? '—'} supervisés`}
              icon={<RadioTower size={20} color="var(--accent)" />}
              iconBg="var(--accent-soft)"
            />
            <KPICard
              title="Disponibilité Réseau"
              value={s ? `${s.availability}%` : '—'}
              subtitle="Moyenne temps réel IA"
              icon={<CheckCircle2 size={20} color="var(--success)" />}
              iconBg="var(--success-bg)"
              valueColor={s && s.availability < 95 ? 'var(--danger)' : 'var(--success)'}
            />
            <KPICard
              title="Sites Critiques IA"
              value={s?.critique ?? '—'}
              subtitle="Anomalie forte détectée"
              icon={<ShieldAlert size={20} color="var(--danger)" />}
              iconBg="var(--danger-bg)"
              valueColor="var(--danger)"
            />
            <KPICard
              title="Sites en Alerte IA"
              value={s?.alertes ?? '—'}
              subtitle="Surveillance requise"
              icon={<AlertTriangle size={20} color="var(--warning)" />}
              iconBg="var(--warning-bg)"
              valueColor="var(--warning)"
            />
            <KPICard
              title="Score de Risque IA"
              value={s ? `${s.ai_risk_score}%` : '—'}
              subtitle={`${s?.anomalies ?? 0} anomalies détectées`}
              icon={<BrainCircuit size={20} color="#7c3aed" />}
              iconBg="rgba(124,58,237,0.08)"
              valueColor="#7c3aed"
            />
            <KPICard
              title="Confiance Modèle"
              value={s ? `${s.ai_confidence}%` : '—'}
              subtitle="Isolation Forest"
              icon={<Activity size={20} color="var(--info)" />}
              iconBg="var(--info-bg)"
            />
          </div>

          {/* ── RÉSUMÉ RÉSEAU ── */}
          <div className="panel" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '24px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
              <div style={{ background: 'var(--accent-soft)', padding: 16, borderRadius: '50%' }}>
                <Map size={32} color="var(--accent)" />
              </div>
              <div>
                <h3 style={{ margin: 0, fontSize: '1.2rem', color: 'var(--text)' }}>Cartographie du Réseau</h3>
                <p style={{ margin: '4px 0 0', color: 'var(--text-muted)' }}>
                  Supervision SIG de l'état des {s?.total_antennes ?? 0} antennes
                </p>
              </div>
            </div>
            <button 
              className="btn btn-primary" 
              onClick={() => navigate('/map')}
              style={{ padding: '12px 24px', fontSize: '1rem', display: 'flex', alignItems: 'center', gap: 8 }}
            >
              <Map size={18} /> Voir détails réseau
            </button>
          </div>

          {/* ── GRAPHIQUE + INCIDENTS ── */}
          <div className="dashboard-bottom-row">
            <div className="panel">
              <h3 className="panel-title"><Activity size={16} /> Évolution Trafic & CPU (7h30)</h3>
              <ResponsiveContainer width="100%" height={220}>
                <AreaChart data={history}>
                  <defs>
                    <linearGradient id="gDebit" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%"  stopColor="var(--success)" stopOpacity={0.25} />
                      <stop offset="95%" stopColor="var(--success)" stopOpacity={0} />
                    </linearGradient>
                    <linearGradient id="gCpu" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%"  stopColor="var(--accent)" stopOpacity={0.15} />
                      <stop offset="95%" stopColor="var(--accent)" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                  <XAxis dataKey="time" stroke="var(--text-light)" fontSize={11} tickLine={false} />
                  <YAxis stroke="var(--text-light)" fontSize={11} tickLine={false} axisLine={false} />
                  <Tooltip content={<ChartTooltip />} />
                  <Area type="monotone" dataKey="debit" name="Débit (Mbps)" stroke="var(--success)" strokeWidth={2} fill="url(#gDebit)" />
                  <Area type="monotone" dataKey="cpu"   name="CPU (%)"       stroke="var(--accent)"  strokeWidth={2} fill="url(#gCpu)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>

            <div className="panel">
              <h3 className="panel-title"><ShieldAlert size={16} color="var(--danger)" /> Derniers Incidents</h3>
              <div className="incidents-list">
                {incidents.length === 0 ? (
                  <div className="empty-state">
                    <CheckCircle2 size={28} color="var(--success)" />
                    <p>Aucun incident actif</p>
                  </div>
                ) : incidents.slice(0, 5).map(inc => (
                  <div key={inc.id} className={`incident-item ${inc.criticite === 'critical' ? '' : 'warning'}`}>
                    <div className="incident-item-header">
                      <span className="incident-title-text">{inc.titre}</span>
                      <span className={`badge badge-${inc.criticite === 'critical' ? 'danger' : 'warning'}`}>
                        {inc.criticite === 'critical' ? 'Critique' : 'Alerte'}
                      </span>
                    </div>
                    <div className="incident-meta">
                      <span>{inc.antenne} — {inc.zone}</span>
                      <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                        <Clock size={11} />
                        {(() => { const s = inc.date_creation; const d = new Date(/[Z+]/.test(s) ? s : s.replace(' ','T')+'Z'); return d.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit', timeZone: 'Africa/Tunis' }); })()}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}
