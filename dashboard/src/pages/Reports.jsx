import React, { useState, useCallback } from 'react';
import {
  FileText, Download, FileCode,
  BarChart2, Clock, CheckCircle2, Loader
} from 'lucide-react';
import axios from 'axios';

import Sidebar from '../components/Sidebar';
import { API_BASE_URL } from '../services/apiConfig';
import { useAuth } from '../auth/AuthContext';
import '../styles/ReportsStyles.css';

const REPORTS = [
  {
    id: 'quotidien',
    title: 'Rapport Quotidien NOC',
    description: 'Résumé de l\'état du réseau : disponibilité, incidents actifs, métriques clés.',
    icon: <FileText size={24} color="var(--accent)" />,
    endpoint: '/rapport/quotidien',
    filename: 'rapport_quotidien.pdf',
    type: 'PDF',
  },
  {
    id: 'incidents',
    title: 'Rapport des Incidents',
    description: 'Liste complète des incidents détectés, leur criticité et leur statut de résolution.',
    icon: <BarChart2 size={24} color="var(--danger)" />,
    endpoint: '/rapport/incidents',
    filename: 'rapport_incidents.pdf',
    type: 'PDF',
  },
  {
    id: 'antennes',
    title: 'Export des Antennes (Excel)',
    description: 'Données techniques complètes de tous les 127 sites (CPU, température, latence, etc.).',
    icon: <FileCode size={24} color="var(--success)" />,
    endpoint: '/rapport/antennes/excel',
    filename: 'antennes_export.xlsx',
    type: 'Excel',
    isExcel: true,
  },
  {
    id: 'ia',
    title: 'Rapport Analyse IA',
    description: 'Résultats de l\'algorithme Isolation Forest : anomalies détectées et scores de risque.',
    icon: <FileCode size={24} color="#7c3aed" />,
    endpoint: '/rapport/ia',
    filename: 'rapport_ia.pdf',
    type: 'PDF',
  },
];

export default function RapportsPage() {
  const { token } = useAuth();
  const [downloading, setDownloading] = useState(null);
  const [done, setDone] = useState({});

  const download = useCallback(async (report) => {
    setDownloading(report.id);
    try {
      const res = await axios.get(`${API_BASE_URL}${report.endpoint}`, {
        headers: { Authorization: `Bearer ${token}` },
        responseType: 'blob',
      });

      const mime = report.isExcel
        ? 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        : 'application/pdf';

      const url = window.URL.createObjectURL(new Blob([res.data], { type: mime }));
      const a = document.createElement('a');
      a.href = url;
      a.download = report.filename;
      a.click();
      window.URL.revokeObjectURL(url);

      setDone(prev => ({ ...prev, [report.id]: true }));
      setTimeout(() => setDone(prev => ({ ...prev, [report.id]: false })), 3000);
    } catch (_) {
      alert('Erreur lors de la génération du rapport. Vérifiez que le backend est actif.');
    } finally {
      setDownloading(null);
    }
  }, [token]);

  return (
    <div style={{ display: 'flex' }}>
      <Sidebar />
      <div className="page-content">
        <div className="page-shell">

          {/* ── HEADER ── */}
          <div className="page-header">
            <div className="page-header-left">
              <h1><FileText size={22} color="var(--accent)" /> Centre de Rapports NOC</h1>
              <p>Génération et export de rapports opérationnels au format PDF et Excel</p>
            </div>
          </div>

          {/* ── INFO BANNER ── */}
          <div className="reports-banner">
            <Clock size={16} color="var(--info)" />
            <span>
              Les rapports sont générés dynamiquement à partir des données en temps réel de la base de données.
            </span>
          </div>

          {/* ── REPORT CARDS ── */}
          <div className="reports-grid">
            {REPORTS.map(report => {
              const isLoading = downloading === report.id;
              const isDone    = done[report.id];
              return (
                <div key={report.id} className="report-card">
                  <div className="report-card-icon">
                    {report.icon}
                  </div>
                  <div className="report-card-body">
                    <div className="report-card-type">
                      <span className={`badge ${report.isExcel ? 'badge-success' : 'badge-info'}`}>
                        {report.type}
                      </span>
                    </div>
                    <h3 className="report-card-title">{report.title}</h3>
                    <p className="report-card-desc">{report.description}</p>
                  </div>
                  <button
                    className={`btn ${isDone ? 'btn-success' : 'btn-primary'}`}
                    onClick={() => download(report)}
                    disabled={isLoading}
                  >
                    {isLoading ? (
                      <><Loader size={14} className="spin" /> Génération…</>
                    ) : isDone ? (
                      <><CheckCircle2 size={14} /> Téléchargé</>
                    ) : (
                      <><Download size={14} /> Télécharger</>
                    )}
                  </button>
                </div>
              );
            })}
          </div>

          {/* ── NOTE ACADÉMIQUE ── */}
          <div className="panel" style={{ background: 'var(--accent-soft)', border: '1px solid rgba(37,99,235,0.15)' }}>
            <h3 className="panel-title"><BarChart2 size={16} /> Note sur le Reporting</h3>
            <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', lineHeight: 1.7 }}>
              Les rapports PDF sont générés par <strong>ReportLab</strong> (bibliothèque Python) côté backend.
              L'export Excel utilise <strong>openpyxl</strong> pour produire des fichiers .xlsx compatibles
              avec Microsoft Excel et LibreOffice. Tous les rapports contiennent un en-tête Tunisie Télécom
              et reflètent l'état du réseau au moment de la génération.
            </p>
          </div>

        </div>
      </div>
    </div>
  );
}
