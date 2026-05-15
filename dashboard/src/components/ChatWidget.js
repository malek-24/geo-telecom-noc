/**
 * ChatWidget.js
 * Mini chat interne flottant pour la communication entre équipes NOC.
 * Utilise le polling simple (GET /chat/messages/new) sans WebSocket.
 */
import React, { useState, useEffect, useRef, useCallback } from 'react';
import { MessageSquare, Send, X, Minimize2, ChevronDown } from 'lucide-react';
import axios from 'axios';
import { API_BASE_URL } from '../services/apiConfig';
import { useAuth } from '../auth/AuthContext';

const POLL_INTERVAL = 5000; // 5 secondes

const ROLE_LABELS = {
  administrateur:    { label: 'Admin',      color: '#7c3aed' },
  ingenieur_reseau:  { label: 'Ingénieur',  color: '#2563eb' },
  ingenieur_reseau:    { label: 'Ingénieur', color: '#059669' },
  technicien_terrain:{ label: 'Technicien', color: '#d97706' },
};

function getRoleStyle(role) {
  return ROLE_LABELS[role] || { label: role, color: '#64748b' };
}

export default function ChatWidget() {
  const { token, username, role } = useAuth();
  const [ouvert, setOuvert] = useState(false);
  const [messages, setMessages] = useState([]);
  const [saisie, setSaisie] = useState('');
  const [envoi, setEnvoi] = useState(false);
  const [nonLus, setNonLus] = useState(0);
  const lastIdRef = useRef(0);
  const bottomRef = useRef(null);
  const inputRef = useRef(null);

  // Chargement initial des messages
  const chargerMessages = useCallback(async () => {
    if (!token) return;
    try {
      const res = await axios.get(`${API_BASE_URL}/chat/messages`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const msgs = res.data || [];
      setMessages(msgs);
      if (msgs.length > 0) {
        lastIdRef.current = msgs[msgs.length - 1].id;
      }
    } catch (_) {}
  }, [token]);

  // Polling des nouveaux messages
  const pollNewMessages = useCallback(async () => {
    if (!token) return;
    try {
      const res = await axios.get(`${API_BASE_URL}/chat/messages/new?since_id=${lastIdRef.current}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const nouveaux = res.data || [];
      if (nouveaux.length > 0) {
        setMessages(prev => [...prev, ...nouveaux]);
        lastIdRef.current = nouveaux[nouveaux.length - 1].id;
        if (!ouvert) {
          setNonLus(prev => prev + nouveaux.length);
        }
      }
    } catch (_) {}
  }, [token, ouvert]);

  useEffect(() => {
    chargerMessages();
  }, [chargerMessages]);

  useEffect(() => {
    const id = setInterval(pollNewMessages, POLL_INTERVAL);
    return () => clearInterval(id);
  }, [pollNewMessages]);

  // Scroll vers le bas quand nouveaux messages
  useEffect(() => {
    if (ouvert && bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, ouvert]);

  const ouvrirChat = () => {
    setOuvert(true);
    setNonLus(0);
    setTimeout(() => inputRef.current?.focus(), 100);
  };

  const envoyerMessage = async (e) => {
    e.preventDefault();
    if (!saisie.trim() || envoi) return;
    setEnvoi(true);
    try {
      const res = await axios.post(`${API_BASE_URL}/chat/messages`,
        { contenu: saisie.trim() },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setMessages(prev => [...prev, res.data]);
      lastIdRef.current = res.data.id;
      setSaisie('');
    } catch (_) {
      alert('Erreur lors de l\'envoi du message.');
    } finally {
      setEnvoi(false);
      inputRef.current?.focus();
    }
  };

  return (
    <>
      {/* Bouton flottant */}
      {!ouvert && (
        <button
          onClick={ouvrirChat}
          title="Chat interne NOC"
          style={{
            position: 'fixed', bottom: 28, right: 28,
            zIndex: 8000,
            width: 54, height: 54, borderRadius: '50%',
            background: 'linear-gradient(135deg, #2563eb, #7c3aed)',
            border: 'none', cursor: 'pointer',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            boxShadow: '0 4px 20px rgba(37,99,235,0.45)',
            transition: 'transform 0.2s, box-shadow 0.2s',
          }}
          onMouseEnter={e => { e.currentTarget.style.transform = 'scale(1.1)'; }}
          onMouseLeave={e => { e.currentTarget.style.transform = 'scale(1)'; }}
        >
          <MessageSquare size={22} color="#fff" />
          {nonLus > 0 && (
            <span style={{
              position: 'absolute', top: 6, right: 6,
              background: '#dc2626', color: '#fff',
              borderRadius: '50%', minWidth: 18, height: 18,
              fontSize: '0.7rem', fontWeight: 700,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              padding: '0 4px'
            }}>
              {nonLus > 9 ? '9+' : nonLus}
            </span>
          )}
        </button>
      )}

      {/* Fenêtre chat */}
      {ouvert && (
        <div style={{
          position: 'fixed', bottom: 28, right: 28,
          zIndex: 8000,
          width: 340, height: 480,
          background: '#0f172a',
          border: '1px solid rgba(255,255,255,0.1)',
          borderRadius: 18,
          boxShadow: '0 16px 60px rgba(0,0,0,0.6)',
          display: 'flex', flexDirection: 'column',
          overflow: 'hidden',
          animation: 'slideUpChat 0.3s ease',
        }}>
          {/* Header */}
          <div style={{
            padding: '14px 18px',
            background: 'linear-gradient(135deg, #1e3a8a, #4c1d95)',
            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <div style={{
                width: 8, height: 8, borderRadius: '50%',
                background: '#22c55e',
                boxShadow: '0 0 6px #22c55e'
              }} />
              <div>
                <div style={{ color: '#fff', fontWeight: 700, fontSize: '0.9rem' }}>
                  Chat NOC Interne
                </div>
                <div style={{ color: 'rgba(255,255,255,0.6)', fontSize: '0.7rem' }}>
                  Tunisie Télécom — Mahdia
                </div>
              </div>
            </div>
            <div style={{ display: 'flex', gap: 6 }}>
              <button
                onClick={() => setOuvert(false)}
                style={{ background: 'rgba(255,255,255,0.1)', border: 'none', borderRadius: 8, padding: 6, cursor: 'pointer', color: '#fff', display: 'flex' }}
              >
                <ChevronDown size={15} />
              </button>
              <button
                onClick={() => setOuvert(false)}
                style={{ background: 'rgba(255,255,255,0.1)', border: 'none', borderRadius: 8, padding: 6, cursor: 'pointer', color: '#fff', display: 'flex' }}
              >
                <X size={15} />
              </button>
            </div>
          </div>

          {/* Messages */}
          <div style={{
            flex: 1, overflowY: 'auto', padding: '14px 14px 8px',
            display: 'flex', flexDirection: 'column', gap: 10,
          }}>
            {messages.length === 0 && (
              <div style={{ textAlign: 'center', color: '#475569', fontSize: '0.82rem', marginTop: 40 }}>
                <MessageSquare size={28} style={{ marginBottom: 8, opacity: 0.4 }} />
                <div>Aucun message pour l'instant.</div>
                <div>Soyez le premier à écrire !</div>
              </div>
            )}
            {messages.map((msg, idx) => {
              const estMoi = msg.auteur_nom === username;
              const rStyle = getRoleStyle(msg.auteur_role);
              return (
                <div key={msg.id || idx} style={{
                  display: 'flex',
                  flexDirection: estMoi ? 'row-reverse' : 'row',
                  gap: 8, alignItems: 'flex-end',
                }}>
                  {/* Avatar */}
                  {!estMoi && (
                    <div style={{
                      width: 28, height: 28, borderRadius: '50%',
                      background: rStyle.color + '22',
                      border: `1.5px solid ${rStyle.color}`,
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      fontSize: '0.65rem', fontWeight: 700, color: rStyle.color,
                      flexShrink: 0,
                    }}>
                      {(msg.auteur_nom || '?').charAt(0).toUpperCase()}
                    </div>
                  )}

                  <div style={{ maxWidth: '78%' }}>
                    {!estMoi && (
                      <div style={{ fontSize: '0.68rem', color: rStyle.color, fontWeight: 600, marginBottom: 3 }}>
                        {msg.auteur_nom} · {rStyle.label}
                      </div>
                    )}
                    <div style={{
                      background: estMoi
                        ? 'linear-gradient(135deg, #2563eb, #7c3aed)'
                        : 'rgba(255,255,255,0.06)',
                      color: estMoi ? '#fff' : '#e2e8f0',
                      borderRadius: estMoi ? '14px 14px 4px 14px' : '14px 14px 14px 4px',
                      padding: '8px 12px',
                      fontSize: '0.82rem', lineHeight: 1.5,
                      wordBreak: 'break-word',
                    }}>
                      {msg.contenu}
                    </div>
                    <div style={{
                      fontSize: '0.62rem', color: '#475569',
                      marginTop: 3,
                      textAlign: estMoi ? 'right' : 'left',
                    }}>
                      {msg.date_envoi ? new Date(msg.date_envoi).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' }) : ''}
                    </div>
                  </div>
                </div>
              );
            })}
            <div ref={bottomRef} />
          </div>

          {/* Saisie */}
          <form
            onSubmit={envoyerMessage}
            style={{
              padding: '10px 14px',
              borderTop: '1px solid rgba(255,255,255,0.07)',
              display: 'flex', gap: 8, alignItems: 'center',
            }}
          >
            <input
              ref={inputRef}
              value={saisie}
              onChange={e => setSaisie(e.target.value)}
              placeholder="Écrire un message..."
              maxLength={500}
              style={{
                flex: 1, background: 'rgba(255,255,255,0.06)',
                border: '1px solid rgba(255,255,255,0.1)',
                borderRadius: 10, padding: '8px 12px',
                color: '#f1f5f9', fontSize: '0.82rem',
                outline: 'none',
              }}
              onFocus={e => e.target.style.borderColor = '#2563eb'}
              onBlur={e => e.target.style.borderColor = 'rgba(255,255,255,0.1)'}
            />
            <button
              type="submit"
              disabled={!saisie.trim() || envoi}
              style={{
                width: 36, height: 36, borderRadius: 10,
                background: saisie.trim() ? 'linear-gradient(135deg, #2563eb, #7c3aed)' : 'rgba(255,255,255,0.06)',
                border: 'none', cursor: saisie.trim() ? 'pointer' : 'default',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                transition: 'background 0.2s', flexShrink: 0,
              }}
            >
              <Send size={15} color={saisie.trim() ? '#fff' : '#475569'} />
            </button>
          </form>
        </div>
      )}

      <style>{`
        @keyframes slideUpChat {
          from { opacity: 0; transform: translateY(20px) scale(0.97); }
          to   { opacity: 1; transform: translateY(0)   scale(1); }
        }
      `}</style>
    </>
  );
}
