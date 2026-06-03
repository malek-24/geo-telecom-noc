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
import { API_BASE_URL, authCfg } from '../services/apiConfig';
import { useAuth } from '../auth/AuthContext';
import { REFRESH_MS } from '../dataRefreshMs';
import { formatTimeTN } from '../utils/dateTime';
import '../styles/DashboardStyles.css';

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

  const [summary, setSummary] = useState(null);
  const [incidents, setIncidents] = useState([]);
  const [history, setHistory] = useState([]);

  const fetchAll = useCallback(async () => {
    if (!token) return;
    const cfg = authCfg(token);
    try {
      const [sRes, iRes, hRes] = await Promise.all([
        axios.get(`${API_BASE_URL}/dashboard/summary`, cfg),
        axios.get(`${API_BASE_URL}/incidents`, cfg),
        axios.get(`${API_BASE_URL}/dashboard/history`, cfg),
      ]);
      setSummary(sRes.data);
      setIncidents(iRes.data.filter(i => i.statut !== 'resolu'));
      setHistory(hRes.data);
    } catch (_) { /* silent fail on poll */ }
  }, [token]);

  useEffect(() => {
    fetchAll();
    const interval = setInterval(fetchAll, REFRESH_MS.dashboard);
    return () => clearInterval(interval);
  }, [fetchAll]);

  const s = summary;

  return (
    <div style={{ display: 'flex' }}>
      <Sidebar />
      <div className="page-content">
        <div className="dashboard-container">

          <div className="dashboard-header">
            <div>
              <h1><Wifi size={22} color="var(--accent)" /> Tableau de Bord NOC</h1>
              <p>Supervision temps réel — Mahdia, Tunisie</p>
            </div>
          </div>

          <div className="dashboard-kpi-grid dashboard-kpi-grid--5">
            <KPICard
              title="Sites Normaux"
              value={s?.en_ligne ?? '—'}
              subtitle={s ? `sur ${s.total_antennes} supervisés` : 'Chargement…'}
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
          </div>

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
              type="button"
              className="btn btn-primary"
              onClick={() => navigate('/map')}
              style={{ padding: '12px 24px', fontSize: '1rem', display: 'flex', alignItems: 'center', gap: 8 }}
            >
              <Map size={18} /> Voir détails réseau
            </button>
          </div>

          <div className="dashboard-bottom-row">
            <div className="panel">
              <h3 className="panel-title"><Activity size={16} /> Disponibilité (12h)</h3>
              {history.length > 0 ? (
                <ResponsiveContainer width="100%" height={220}>
                  <AreaChart data={history}>
                    <defs>
                      <linearGradient id="gDispo" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="var(--success)" stopOpacity={0.25} />
                        <stop offset="95%" stopColor="var(--success)" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                    <XAxis dataKey="time" stroke="var(--text-light)" fontSize={11} tickLine={false} />
                    <YAxis stroke="var(--text-light)" fontSize={11} tickLine={false} axisLine={false} domain={[0, 100]} />
                    <Tooltip content={<ChartTooltip />} />
                    <Area
                      type="monotone"
                      dataKey="disponibilite"
                      name="Disponibilité (%)"
                      stroke="var(--success)"
                      strokeWidth={2}
                      fill="url(#gDispo)"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              ) : (
                <div className="empty-state" style={{ height: 220, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>Aucune donnée sur les 12 dernières heures.</p>
                </div>
              )}
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
                        {formatTimeTN(inc.date_creation)}
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
