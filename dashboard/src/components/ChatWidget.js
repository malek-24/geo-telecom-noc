/**
 * ChatWidget.js — Chat interne NOC avec messagerie privée
 * Canal Public + Conversations Privées entre utilisateurs.
 */
import React, { useState, useEffect, useRef, useCallback } from 'react';
import { MessageSquare, Send, X, ChevronDown, Lock, Users, ArrowLeft } from 'lucide-react';
import axios from 'axios';
import { API_BASE_URL } from '../services/apiConfig';
import { useAuth } from '../auth/AuthContext';

const POLL_MS = 5000;

const ROLE_COLORS = {
  administrateur:    '#7c3aed',
  ingenieur_reseau:  '#2563eb',
  technicien_terrain:'#d97706',
};

function getRoleColor(role) {
  return ROLE_COLORS[role] || '#64748b';
}

function RoleTag({ role }) {
  const labels = {
    administrateur:    'Admin',
    ingenieur_reseau:  'Ingénieur',
    technicien_terrain:'Technicien',
  };
  const color = getRoleColor(role);
  return (
    <span style={{
      background: color + '22', color,
      fontSize: '0.65rem', fontWeight: 700,
      padding: '1px 6px', borderRadius: 20,
    }}>
      {labels[role] || role}
    </span>
  );
}

export default function ChatWidget() {
  const { token, username, role, user } = useAuth();
  const [ouvert, setOuvert] = useState(false);
  // 'public' | { id, username, fullname }
  const [canal, setCanal] = useState('public');
  const [vue, setVue] = useState('canal'); // 'canal' | 'users'
  const [messages, setMessages] = useState([]);
  const [utilisateurs, setUtilisateurs] = useState([]);
  const [saisie, setSaisie] = useState('');
  const [envoi, setEnvoi] = useState(false);
  const [nonLus, setNonLus] = useState(0);
  const lastIdRef = useRef(0);
  const bottomRef = useRef(null);
  const inputRef  = useRef(null);

  // ── Chargement messages ────────────────────────────────────
  const chargerMessages = useCallback(async () => {
    if (!token) return;
    try {
      const url = canal === 'public'
        ? `${API_BASE_URL}/chat/messages`
        : `${API_BASE_URL}/chat/private/${canal.id}`;

      const res = await axios.get(url, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const msgs = res.data || [];
      setMessages(msgs);
      if (msgs.length > 0) lastIdRef.current = msgs[msgs.length - 1].id;
    } catch (_) {}
  }, [token, canal]);

  // ── Polling nouveaux messages ──────────────────────────────
  const pollMessages = useCallback(async () => {
    if (!token) return;
    try {
      const url = canal === 'public'
        ? `${API_BASE_URL}/chat/messages/new?since_id=${lastIdRef.current}`
        : `${API_BASE_URL}/chat/private/${canal.id}/new?since_id=${lastIdRef.current}`;

      const res = await axios.get(url, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const nouveaux = res.data || [];
      if (nouveaux.length > 0) {
        setMessages(prev => [...prev, ...nouveaux]);
        lastIdRef.current = nouveaux[nouveaux.length - 1].id;
        if (!ouvert) setNonLus(prev => prev + nouveaux.length);
      }
    } catch (_) {}
  }, [token, canal, ouvert]);

  // ── Chargement liste utilisateurs ─────────────────────────
  const chargerUtilisateurs = useCallback(async () => {
    if (!token) return;
    try {
      const res = await axios.get(`${API_BASE_URL}/chat/users`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setUtilisateurs(res.data || []);
    } catch (_) {}
  }, [token]);

  useEffect(() => { chargerMessages(); }, [chargerMessages]);
  useEffect(() => {
    const id = setInterval(pollMessages, POLL_MS);
    return () => clearInterval(id);
  }, [pollMessages]);
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

  const changerCanal = (nouveauCanal) => {
    setCanal(nouveauCanal);
    setMessages([]);
    lastIdRef.current = 0;
    setVue('canal');
  };

  const ouvrirListeUsers = () => {
    chargerUtilisateurs();
    setVue('users');
  };

  // ── Envoi message ──────────────────────────────────────────
  const envoyerMessage = async (e) => {
    e.preventDefault();
    if (!saisie.trim() || envoi) return;
    setEnvoi(true);
    try {
      const url = canal === 'public'
        ? `${API_BASE_URL}/chat/messages`
        : `${API_BASE_URL}/chat/private/${canal.id}`;

      const res = await axios.post(url,
        { contenu: saisie.trim() },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setMessages(prev => [...prev, res.data]);
      lastIdRef.current = res.data.id;
      setSaisie('');
    } catch (_) {
      alert("Erreur lors de l'envoi du message.");
    } finally {
      setEnvoi(false);
      inputRef.current?.focus();
    }
  };

  // ── Titre de l'en-tête ─────────────────────────────────────
  const headerTitle = canal === 'public'
    ? 'Chat NOC — Canal Public'
    : `💬 ${canal.fullname || canal.username}`;

  const headerSub = canal === 'public'
    ? 'Tunisie Télécom — Mahdia'
    : 'Conversation privée';

  return (
    <>
      {/* Bouton flottant */}
      {!ouvert && (
        <button
          onClick={ouvrirChat}
          title="Chat interne NOC"
          style={{
            position: 'fixed', bottom: 28, right: 28, zIndex: 8000,
            width: 54, height: 54, borderRadius: '50%',
            background: 'linear-gradient(135deg, #2563eb, #7c3aed)',
            border: 'none', cursor: 'pointer',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            boxShadow: '0 4px 20px rgba(37,99,235,0.45)',
            transition: 'transform 0.2s',
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
          position: 'fixed', bottom: 28, right: 28, zIndex: 8000,
          width: 360, height: 520,
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
            padding: '12px 16px',
            background: 'linear-gradient(135deg, #1e3a8a, #4c1d95)',
            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              {canal !== 'public' && (
                <button
                  onClick={() => changerCanal('public')}
                  style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#fff', display: 'flex', padding: 0 }}
                >
                  <ArrowLeft size={16} />
                </button>
              )}
              <div style={{ width: 8, height: 8, borderRadius: '50%', background: '#22c55e', boxShadow: '0 0 6px #22c55e' }} />
              <div>
                <div style={{ color: '#fff', fontWeight: 700, fontSize: '0.87rem' }}>{headerTitle}</div>
                <div style={{ color: 'rgba(255,255,255,0.55)', fontSize: '0.68rem' }}>{headerSub}</div>
              </div>
            </div>
            <div style={{ display: 'flex', gap: 6 }}>
              {/* Bouton utilisateurs */}
              <button
                onClick={ouvrirListeUsers}
                title="Messages privés"
                style={{ background: 'rgba(255,255,255,0.1)', border: 'none', borderRadius: 8, padding: 6, cursor: 'pointer', color: '#fff', display: 'flex' }}
              >
                <Lock size={14} />
              </button>
              {/* Bouton canal public */}
              {canal !== 'public' && (
                <button
                  onClick={() => changerCanal('public')}
                  title="Canal public"
                  style={{ background: 'rgba(255,255,255,0.1)', border: 'none', borderRadius: 8, padding: 6, cursor: 'pointer', color: '#fff', display: 'flex' }}
                >
                  <Users size={14} />
                </button>
              )}
              <button
                onClick={() => setOuvert(false)}
                style={{ background: 'rgba(255,255,255,0.1)', border: 'none', borderRadius: 8, padding: 6, cursor: 'pointer', color: '#fff', display: 'flex' }}
              >
                <ChevronDown size={14} />
              </button>
              <button
                onClick={() => setOuvert(false)}
                style={{ background: 'rgba(255,255,255,0.1)', border: 'none', borderRadius: 8, padding: 6, cursor: 'pointer', color: '#fff', display: 'flex' }}
              >
                <X size={14} />
              </button>
            </div>
          </div>

          {/* Vue : Liste des utilisateurs */}
          {vue === 'users' && (
            <div style={{ flex: 1, overflowY: 'auto', padding: 12 }}>
              <div style={{ color: 'rgba(255,255,255,0.5)', fontSize: '0.72rem', marginBottom: 10, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Choisir un destinataire
              </div>
              {utilisateurs.length === 0 ? (
                <div style={{ color: '#475569', textAlign: 'center', marginTop: 30, fontSize: '0.82rem' }}>
                  Aucun autre utilisateur actif.
                </div>
              ) : utilisateurs.map(u => (
                <button
                  key={u.id}
                  onClick={() => changerCanal(u)}
                  style={{
                    width: '100%', textAlign: 'left',
                    background: canal !== 'public' && canal.id === u.id
                      ? 'rgba(37,99,235,0.2)'
                      : 'rgba(255,255,255,0.04)',
                    border: '1px solid rgba(255,255,255,0.07)',
                    borderRadius: 10, padding: '10px 12px',
                    cursor: 'pointer', marginBottom: 6,
                    display: 'flex', alignItems: 'center', gap: 10,
                    color: '#e2e8f0',
                    transition: 'background 0.15s',
                  }}
                  onMouseEnter={e => { e.currentTarget.style.background = 'rgba(37,99,235,0.15)'; }}
                  onMouseLeave={e => { e.currentTarget.style.background = canal !== 'public' && canal.id === u.id ? 'rgba(37,99,235,0.2)' : 'rgba(255,255,255,0.04)'; }}
                >
                  <div style={{
                    width: 32, height: 32, borderRadius: '50%',
                    background: getRoleColor(u.role) + '33',
                    border: `2px solid ${getRoleColor(u.role)}`,
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontSize: '0.8rem', fontWeight: 700, color: getRoleColor(u.role),
                    flexShrink: 0,
                  }}>
                    {(u.fullname || u.username).charAt(0).toUpperCase()}
                  </div>
                  <div>
                    <div style={{ fontWeight: 600, fontSize: '0.85rem' }}>{u.fullname || u.username}</div>
                    <RoleTag role={u.role} />
                  </div>
                  <Lock size={12} style={{ marginLeft: 'auto', opacity: 0.4 }} color="#fff" />
                </button>
              ))}
              <button
                onClick={() => setVue('canal')}
                style={{
                  width: '100%', marginTop: 8, padding: '8px',
                  background: 'none', border: '1px solid rgba(255,255,255,0.1)',
                  borderRadius: 10, color: 'rgba(255,255,255,0.5)',
                  cursor: 'pointer', fontSize: '0.8rem',
                }}
              >
                ← Retour au canal
              </button>
            </div>
          )}

          {/* Vue : Canal messages */}
          {vue === 'canal' && (
            <>
              <div style={{ flex: 1, overflowY: 'auto', padding: '12px 12px 6px', display: 'flex', flexDirection: 'column', gap: 8 }}>
                {messages.length === 0 && (
                  <div style={{ textAlign: 'center', color: '#475569', fontSize: '0.8rem', marginTop: 40 }}>
                    <MessageSquare size={26} style={{ marginBottom: 8, opacity: 0.4 }} />
                    <div>{canal === 'public' ? 'Aucun message.' : 'Commencez la conversation !'}</div>
                  </div>
                )}
                {messages.map((msg, idx) => {
                  const estMoi = msg.auteur_nom === username;
                  const color  = getRoleColor(msg.auteur_role);
                  return (
                    <div key={msg.id || idx} style={{ display: 'flex', flexDirection: estMoi ? 'row-reverse' : 'row', gap: 7, alignItems: 'flex-end' }}>
                      {!estMoi && (
                        <div style={{
                          width: 26, height: 26, borderRadius: '50%',
                          background: color + '22', border: `1.5px solid ${color}`,
                          display: 'flex', alignItems: 'center', justifyContent: 'center',
                          fontSize: '0.62rem', fontWeight: 700, color,
                          flexShrink: 0,
                        }}>
                          {(msg.auteur_nom || '?').charAt(0).toUpperCase()}
                        </div>
                      )}
                      <div style={{ maxWidth: '78%' }}>
                        {!estMoi && (
                          <div style={{ display: 'flex', alignItems: 'center', gap: 5, marginBottom: 3 }}>
                            <span style={{ fontSize: '0.68rem', color, fontWeight: 600 }}>{msg.auteur_nom}</span>
                            <RoleTag role={msg.auteur_role} />
                          </div>
                        )}
                        <div style={{
                          background: estMoi
                            ? 'linear-gradient(135deg, #2563eb, #7c3aed)'
                            : 'rgba(255,255,255,0.06)',
                          color: estMoi ? '#fff' : '#e2e8f0',
                          borderRadius: estMoi ? '14px 14px 4px 14px' : '14px 14px 14px 4px',
                          padding: '7px 12px', fontSize: '0.82rem', lineHeight: 1.5,
                          wordBreak: 'break-word',
                        }}>
                          {msg.contenu}
                        </div>
                        <div style={{ fontSize: '0.6rem', color: '#475569', marginTop: 2, textAlign: estMoi ? 'right' : 'left' }}>
                          {msg.date_envoi ? new Date(msg.date_envoi).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' }) : ''}
                        </div>
                      </div>
                    </div>
                  );
                })}
                <div ref={bottomRef} />
              </div>

              {/* Saisie */}
              <form onSubmit={envoyerMessage} style={{ padding: '8px 12px', borderTop: '1px solid rgba(255,255,255,0.07)', display: 'flex', gap: 8, alignItems: 'center' }}>
                <input
                  ref={inputRef}
                  value={saisie}
                  onChange={e => setSaisie(e.target.value)}
                  placeholder={canal === 'public' ? "Message au canal public…" : `Message privé à ${canal.username || ''}…`}
                  maxLength={500}
                  style={{
                    flex: 1, background: 'rgba(255,255,255,0.06)',
                    border: '1px solid rgba(255,255,255,0.1)',
                    borderRadius: 10, padding: '7px 11px',
                    color: '#f1f5f9', fontSize: '0.82rem', outline: 'none',
                  }}
                  onFocus={e  => { e.target.style.borderColor = '#2563eb'; }}
                  onBlur={e   => { e.target.style.borderColor = 'rgba(255,255,255,0.1)'; }}
                />
                <button
                  type="submit"
                  disabled={!saisie.trim() || envoi}
                  style={{
                    width: 34, height: 34, borderRadius: 10, flexShrink: 0,
                    background: saisie.trim() ? 'linear-gradient(135deg, #2563eb, #7c3aed)' : 'rgba(255,255,255,0.06)',
                    border: 'none', cursor: saisie.trim() ? 'pointer' : 'default',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    transition: 'background 0.2s',
                  }}
                >
                  <Send size={14} color={saisie.trim() ? '#fff' : '#475569'} />
                </button>
              </form>
            </>
          )}
        </div>
      )}

      <style>{`
        @keyframes slideUpChat {
          from { opacity: 0; transform: translateY(20px) scale(0.97); }
          to   { opacity: 1; transform: translateY(0) scale(1); }
        }
      `}</style>
    </>
  );
}
