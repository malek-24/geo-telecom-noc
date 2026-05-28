import React, { useState, useCallback } from 'react';
import {
  FileText, Download, FileCode,
  BarChart2, CheckCircle2, Loader
} from 'lucide-react';
import axios from 'axios';

import Sidebar from '../components/Sidebar';
import { API_BASE_URL, authCfg } from '../services/apiConfig';
import { useAuth } from '../auth/AuthContext';
import { downloadCsv } from '../services/exportCsv';
import '../styles/ReportsStyles.css';

const REPORTS = [
  {
    id: 'quotidien',
    title: 'Rapport quotidien NOC',
    icon: <FileText size={24} color="var(--accent)" />,
    endpoint: '/rapport/quotidien',
    filename: 'rapport_quotidien.pdf',
    type: 'PDF',
  },
  {
    id: 'incidents',
    title: 'Rapport incidents',
    icon: <BarChart2 size={24} color="var(--danger)" />,
    endpoint: '/rapport/incidents',
    filename: 'rapport_incidents.pdf',
    type: 'PDF',
  },
  {
    id: 'antennes',
    title: 'Export antennes (Excel)',
    icon: <FileCode size={24} color="var(--success)" />,
    endpoint: '/rapport/antennes/excel',
    filename: 'antennes_export.xlsx',
    type: 'Excel',
    isExcel: true,
  },
  {
    id: 'ia',
    title: 'Rapport analyse IA',
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
  const [exportingCsv, setExportingCsv] = useState(false);

  const handleExportMesuresCsv = async () => {
    setExportingCsv(true);
    try {
      await downloadCsv(token, '/export/mesures', 'export_mesures.csv');
    } catch (_) {
      alert('Erreur export CSV mesures.');
    } finally {
      setExportingCsv(false);
    }
  };

  const download = useCallback(async (report) => {
    setDownloading(report.id);
    try {
      const res = await axios.get(`${API_BASE_URL}${report.endpoint}`, {
        ...authCfg(token),
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
              <h1><FileText size={22} color="var(--accent)" /> Rapports NOC</h1>
            </div>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={handleExportMesuresCsv}
              disabled={exportingCsv}
            >
              <Download size={16} /> {exportingCsv ? 'Export…' : 'Exporter CSV'}
            </button>
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

        </div>
      </div>
    </div>
  );
}
