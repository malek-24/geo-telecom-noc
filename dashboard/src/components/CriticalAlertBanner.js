/**
 * CriticalAlertBanner.js
 * Popup de notification temps réel pour les antennes critiques détectées par l'IA.
 * Polling toutes les 45 secondes vers /alerts/critical
 */
import React, { useState, useEffect, useRef, useCallback } from 'react';
import { AlertTriangle, X, Radio, ExternalLink } from 'lucide-react';
import axios from 'axios';
import { API_BASE_URL } from '../services/apiConfig';
import { useAuth } from '../auth/AuthContext';
import { useNavigate } from 'react-router-dom';

const POLL_INTERVAL = 45000; // 45 secondes

const ROLE_COLORS = {
  critique: { bg: '#fef2f2', border: '#dc2626', text: '#dc2626', badgeBg: '#dc2626' },
  alerte:   { bg: '#fffbeb', border: '#d97706', text: '#d97706', badgeBg: '#d97706' },
};

export default function CriticalAlertBanner() {
  const { token } = useAuth();
  const navigate = useNavigate();
  const [alertes, setAlertes] = useState([]);
  const [visible, setVisible] = useState(false);
  const [dismissed, setDismissed] = useState(new Set());
  const lastSeenIds = useRef(new Set());
  const audioRef = useRef(null);

  const fetchCritical = useCallback(async () => {
    if (!token) return;
    try {
      const res = await axios.get(`${API_BASE_URL}/alerts/critical`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const data = res.data || [];

      // Ne montrer que les nouvelles alertes jamais vues
      const nouvelles = data.filter(a => !lastSeenIds.current.has(a.id));
      if (nouvelles.length > 0) {
        nouvelles.forEach(a => lastSeenIds.current.add(a.id));
        setAlertes(nouvelles);
        setDismissed(new Set());
        setVisible(true);

        // Son de notification (optionnel — peut échouer silencieusement)
        try {
          if (!audioRef.current) {
            audioRef.current = new Audio('data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAA...');
          }
          audioRef.current.volume = 0.3;
          audioRef.current.play().catch(() => {});
        } catch (_) {}
      }
    } catch (_) {}
  }, [token]);

  useEffect(() => {
    fetchCritical();
    const id = setInterval(fetchCritical, POLL_INTERVAL);
    return () => clearInterval(id);
  }, [fetchCritical]);

  const dismissAlerte = (alerteId) => {
    const newDismissed = new Set(dismissed);
    newDismissed.add(alerteId);
    setDismissed(newDismissed);
    if (newDismissed.size >= alertes.length) {
      setTimeout(() => setVisible(false), 300);
    }
  };

  const dismissAll = () => {
    setVisible(false);
    setDismissed(new Set(alertes.map(a => a.id)));
  };

  if (!visible || alertes.length === 0) return null;

  const alertesVisibles = alertes.filter(a => !dismissed.has(a.id));
  if (alertesVisibles.length === 0) return null;

  return (
    <>
      {/* Overlay sombre léger */}
      <div
        onClick={dismissAll}
        style={{
          position: 'fixed', inset: 0, zIndex: 9998,
          background: 'rgba(0,0,0,0.3)',
          animation: 'fadeIn 0.25s ease'
        }}
      />

      {/* Conteneur des alertes */}
      <div style={{
        position: 'fixed',
        top: 24, right: 24,
        zIndex: 9999,
        display: 'flex', flexDirection: 'column', gap: 12,
        maxWidth: 400, width: '90vw',
      }}>
        {alertesVisibles.slice(0, 3).map((alerte, idx) => {
          const colors = ROLE_COLORS.critique;
          return (
            <div
              key={alerte.id}
              style={{
                background: '#0f172a',
                border: `2px solid ${colors.border}`,
                borderRadius: 14,
                padding: '18px 20px',
                boxShadow: `0 8px 40px rgba(220,38,38,0.35)`,
                animation: `slideInRight 0.35s ease ${idx * 0.08}s both`,
                position: 'relative',
              }}
            >
              {/* Barre supérieure */}
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <div style={{
                    width: 34, height: 34, borderRadius: '50%',
                    background: 'rgba(220,38,38,0.15)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    animation: 'pulse 1.5s infinite'
                  }}>
                    <AlertTriangle size={18} color={colors.border} />
                  </div>
                  <div>
                    <div style={{ fontWeight: 700, fontSize: '0.85rem', color: colors.border }}>
                      ALERTE CRITIQUE — IA
                    </div>
                    <div style={{ fontSize: '0.7rem', color: '#94a3b8' }}>
                      Isolation Forest • {new Date(alerte.date_creation).toLocaleTimeString('fr-FR')}
                    </div>
                  </div>
                </div>
                <button
                  onClick={() => dismissAlerte(alerte.id)}
                  style={{
                    background: 'rgba(255,255,255,0.06)', border: 'none', borderRadius: 8,
                    cursor: 'pointer', padding: 6, color: '#94a3b8', display: 'flex'
                  }}
                >
                  <X size={16} />
                </button>
              </div>

              {/* Contenu */}
              <div style={{ display: 'flex', alignItems: 'flex-start', gap: 10 }}>
                <Radio size={16} color={colors.border} style={{ flexShrink: 0, marginTop: 3 }} />
                <div>
                  <div style={{ fontWeight: 700, color: '#f1f5f9', fontSize: '0.95rem', marginBottom: 4 }}>
                    {alerte.nom}
                  </div>
                  <div style={{ fontSize: '0.78rem', color: '#94a3b8', marginBottom: 6 }}>
                    Zone : {alerte.zone}
                  </div>
                  <div style={{
                    fontSize: '0.8rem', color: '#cbd5e1',
                    background: 'rgba(220,38,38,0.1)',
                    borderRadius: 6, padding: '6px 10px',
                    lineHeight: 1.5
                  }}>
                    {alerte.titre || alerte.type_anomalie || 'Anomalie critique détectée'}
                  </div>
                </div>
              </div>

              {/* Actions */}
              <div style={{ display: 'flex', gap: 8, marginTop: 14 }}>
                <button
                  onClick={() => { navigate('/moderation'); dismissAlerte(alerte.id); }}
                  style={{
                    flex: 1, padding: '8px 12px', borderRadius: 8,
                    background: colors.border, color: '#fff',
                    border: 'none', cursor: 'pointer',
                    fontWeight: 600, fontSize: '0.8rem',
                    display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6
                  }}
                >
                  <ExternalLink size={13} /> Voir l'incident
                </button>
                <button
                  onClick={() => dismissAlerte(alerte.id)}
                  style={{
                    padding: '8px 14px', borderRadius: 8,
                    background: 'rgba(255,255,255,0.06)', color: '#94a3b8',
                    border: '1px solid rgba(255,255,255,0.08)', cursor: 'pointer',
                    fontSize: '0.8rem'
                  }}
                >
                  Fermer
                </button>
              </div>
            </div>
          );
        })}

        {/* Badge si plus de 3 */}
        {alertesVisibles.length > 3 && (
          <div style={{
            textAlign: 'center', color: '#dc2626',
            fontSize: '0.8rem', fontWeight: 600,
            background: 'rgba(220,38,38,0.1)',
            borderRadius: 8, padding: '8px 12px',
            border: '1px solid rgba(220,38,38,0.2)'
          }}>
            +{alertesVisibles.length - 3} autres incidents critiques
          </div>
        )}
      </div>

      <style>{`
        @keyframes slideInRight {
          from { opacity: 0; transform: translateX(60px) scale(0.97); }
          to   { opacity: 1; transform: translateX(0)   scale(1); }
        }
        @keyframes fadeIn {
          from { opacity: 0; }
          to   { opacity: 1; }
        }
        @keyframes pulse {
          0%, 100% { box-shadow: 0 0 0 0 rgba(220,38,38,0.4); }
          50%       { box-shadow: 0 0 0 8px rgba(220,38,38,0); }
        }
      `}</style>
    </>
  );
}
