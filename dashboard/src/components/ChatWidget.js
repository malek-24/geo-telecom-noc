/**
 * ChatWidget.js — Messagerie NOC (canal public + privé)
 */
import React, { useState, useEffect, useRef, useCallback } from 'react';
import { MessageSquare, Send, X, Lock, Users, ArrowLeft } from 'lucide-react';
import axios from 'axios';
import { API_BASE_URL, authCfg } from '../services/apiConfig';
import { useAuth } from '../auth/AuthContext';
import { REFRESH_MS } from '../dataRefreshMs';
import { formatDateTimeTN } from '../utils/dateTime';
import './ChatWidget.css';

const ROLE_COLORS = {
  administrateur: '#7c3aed',
  ingenieur_reseau: '#2563eb',
  technicien_terrain: '#d97706',
};

function getRoleColor(role) {
  return ROLE_COLORS[role] || '#64748b';
}

function RoleTag({ role }) {
  const labels = {
    administrateur: 'Admin',
    ingenieur_reseau: 'Ingénieur',
    technicien_terrain: 'Technicien',
  };
  const color = getRoleColor(role);
  return (
    <span className="chat-role-tag" style={{ background: `${color}18`, color }}>
      {labels[role] || role}
    </span>
  );
}

function messageErreur(err) {
  if (!err.response) {
    return 'Connexion perdue. Vérifiez le réseau ou que l\'API est démarrée.';
  }
  const status = err.response.status;
  const msg = err.response.data?.error;
  if (status === 400) return msg || 'Message invalide.';
  if (status === 404) return msg || 'Destinataire introuvable.';
  if (status === 401) return 'Session expirée. Reconnectez-vous.';
  if (status === 403) return msg || 'Action non autorisée.';
  if (status >= 500) return msg || 'Erreur serveur. Réessayez plus tard.';
  return msg || "Erreur lors de l'envoi du message.";
}

function estMonMessage(msg, userId, username) {
  if (userId && msg.auteur_id) return Number(msg.auteur_id) === Number(userId);
  return msg.auteur_nom === username;
}

export default function ChatWidget() {
  const { token, username, role, userId } = useAuth();
  const [ouvert, setOuvert] = useState(false);
  const [canal, setCanal] = useState('public');
  const [vue, setVue] = useState('canal');
  const [messages, setMessages] = useState([]);
  const [utilisateurs, setUtilisateurs] = useState([]);
  const [saisie, setSaisie] = useState('');
  const [envoi, setEnvoi] = useState(false);
  const [erreurEnvoi, setErreurEnvoi] = useState('');
  const [nonLus, setNonLus] = useState(0);
  const [nonLusParPeer, setNonLusParPeer] = useState({});
  const lastIdRef = useRef(0);
  const bottomRef = useRef(null);
  const inputRef = useRef(null);
  const notifPermission = useRef(
    typeof Notification !== 'undefined' ? Notification.permission : 'denied'
  );
  const prevUnreadTotal = useRef(0);

  const marquerConversationLue = useCallback(async () => {
    if (!token) return;
    try {
      if (canal === 'public') {
        await axios.post(`${API_BASE_URL}/chat/messages/read`, {}, authCfg(token));
      } else if (canal?.id) {
        await axios.post(`${API_BASE_URL}/chat/private/${canal.id}/read`, {}, authCfg(token));
      }
      setNonLusParPeer(prev => {
        const next = { ...prev };
        if (canal === 'public') next.public = 0;
        else if (canal?.id) next[canal.id] = 0;
        return next;
      });
    } catch (_) {}
  }, [token, canal]);

  const fetchUnreadSummary = useCallback(async () => {
    if (!token) return;
    try {
      const res = await axios.get(`${API_BASE_URL}/chat/unread/summary`, authCfg(token));
      const total = res.data?.total ?? 0;
      if (
        !ouvert
        && total > prevUnreadTotal.current
        && prevUnreadTotal.current > 0
        && typeof Notification !== 'undefined'
        && notifPermission.current === 'granted'
      ) {
        try {
          new Notification('Nouveau message NOC', {
            body: `Vous avez ${total} message(s) non lu(s).`,
            icon: '/logo-noc.svg',
          });
        } catch (_) {}
      }
      prevUnreadTotal.current = total;
      setNonLus(total);
      const map = { public: res.data?.public ?? 0 };
      (res.data?.par_expediteur || []).forEach(row => {
        map[row.auteur_id] = row.count;
      });
      setNonLusParPeer(map);
    } catch (_) {}
  }, [token, ouvert]);

  const notifierNouveauMessage = useCallback((msg) => {
    if (ouvert) return;
    if (estMonMessage(msg, userId, username)) return;
    const titre = canal === 'public'
      ? `Nouveau message — ${msg.auteur_nom || 'NOC'}`
      : `Message de ${msg.auteur_nom || 'un utilisateur'}`;
    const body = (msg.contenu || '').slice(0, 120);
    if (typeof Notification !== 'undefined' && notifPermission.current === 'granted') {
      try {
        new Notification(titre, { body, icon: '/logo-noc.svg' });
      } catch (_) {}
    }
  }, [ouvert, canal, userId, username]);

  const chargerMessages = useCallback(async () => {
    if (!token) return;
    try {
      const url = canal === 'public'
        ? `${API_BASE_URL}/chat/messages`
        : `${API_BASE_URL}/chat/private/${canal.id}`;
      const res = await axios.get(url, authCfg(token));
      const msgs = res.data || [];
      setMessages(msgs);
      if (msgs.length > 0) lastIdRef.current = msgs[msgs.length - 1].id;
      await marquerConversationLue();
      await fetchUnreadSummary();
    } catch (_) {}
  }, [token, canal, marquerConversationLue, fetchUnreadSummary]);

  const pollMessages = useCallback(async () => {
    if (!token) return;
    try {
      const url = canal === 'public'
        ? `${API_BASE_URL}/chat/messages/new?since_id=${lastIdRef.current}`
        : `${API_BASE_URL}/chat/private/${canal.id}/new?since_id=${lastIdRef.current}`;
      const res = await axios.get(url, authCfg(token));
      const nouveaux = res.data || [];
      if (nouveaux.length > 0) {
        setMessages(prev => [...prev, ...nouveaux]);
        lastIdRef.current = nouveaux[nouveaux.length - 1].id;
        nouveaux.forEach(msg => {
          if (!estMonMessage(msg, userId, username)) {
            if (!ouvert || (canal !== 'public' && vue !== 'canal')) {
              notifierNouveauMessage(msg);
            }
          }
        });
        if (ouvert && vue === 'canal') {
          await marquerConversationLue();
        } else {
          await fetchUnreadSummary();
        }
      }
    } catch (_) {}
  }, [token, canal, ouvert, vue, userId, username, marquerConversationLue, fetchUnreadSummary, notifierNouveauMessage]);

  const chargerUtilisateurs = useCallback(async () => {
    if (!token) return;
    try {
      const res = await axios.get(`${API_BASE_URL}/chat/users`, authCfg(token));
      setUtilisateurs(res.data || []);
    } catch (_) {}
  }, [token]);

  useEffect(() => { fetchUnreadSummary(); }, [fetchUnreadSummary]);
  useEffect(() => {
    const id = setInterval(fetchUnreadSummary, REFRESH_MS.chat);
    return () => clearInterval(id);
  }, [fetchUnreadSummary]);

  useEffect(() => { chargerMessages(); }, [chargerMessages]);
  useEffect(() => {
    const id = setInterval(pollMessages, REFRESH_MS.chat);
    return () => clearInterval(id);
  }, [pollMessages]);

  useEffect(() => {
    if (ouvert && bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, ouvert]);

  const ouvrirChat = async () => {
    if (typeof Notification !== 'undefined' && Notification.permission === 'default') {
      try {
        notifPermission.current = await Notification.requestPermission();
      } catch (_) {}
    }
    setOuvert(true);
    setErreurEnvoi('');
    await marquerConversationLue();
    await fetchUnreadSummary();
    setTimeout(() => inputRef.current?.focus(), 100);
  };

  const changerCanal = async (nouveauCanal) => {
    setCanal(nouveauCanal);
    setMessages([]);
    lastIdRef.current = 0;
    setVue('canal');
    setErreurEnvoi('');
  };

  const ouvrirListeUsers = () => {
    chargerUtilisateurs();
    setVue('users');
  };

  const envoyerMessage = async (e) => {
    e.preventDefault();
    const texte = saisie.trim();
    if (!texte || envoi) return;

    if (canal !== 'public' && (!canal.id || canal.id <= 0)) {
      setErreurEnvoi('Destinataire invalide.');
      return;
    }

    setEnvoi(true);
    setErreurEnvoi('');
    try {
      const url = canal === 'public'
        ? `${API_BASE_URL}/chat/messages`
        : `${API_BASE_URL}/chat/private/${canal.id}`;

      const res = await axios.post(url, { contenu: texte }, authCfg(token));
      const msg = {
        ...res.data,
        auteur_id: res.data.auteur_id ?? userId,
        auteur_nom: res.data.auteur_nom ?? username,
        auteur_role: res.data.auteur_role ?? role,
      };
      setMessages(prev => [...prev, msg]);
      lastIdRef.current = res.data.id;
      setSaisie('');
    } catch (err) {
      setErreurEnvoi(messageErreur(err));
    } finally {
      setEnvoi(false);
      inputRef.current?.focus();
    }
  };

  const headerTitle = canal === 'public'
    ? 'Chat NOC — Canal public'
    : (canal.fullname || canal.username);

  const headerSub = canal === 'public'
    ? 'Tunisie Télécom — Mahdia'
    : 'Conversation privée';

  const badgeCount = nonLus > 99 ? '99+' : nonLus;

  return (
    <>
      {!ouvert && (
        <button type="button" className="chat-fab" onClick={ouvrirChat} title="Messagerie NOC">
          <MessageSquare size={22} color="#fff" />
          {nonLus > 0 && <span className="chat-fab-badge">{badgeCount}</span>}
        </button>
      )}

      {ouvert && (
        <div className="chat-panel">
          <div className="chat-header">
            <div className="chat-header-left">
              {canal !== 'public' && (
                <button type="button" className="chat-icon-btn" onClick={() => changerCanal('public')} aria-label="Retour">
                  <ArrowLeft size={16} />
                </button>
              )}
              <div className="chat-status-dot" />
              <div>
                <div className="chat-header-title">{headerTitle}</div>
                <div className="chat-header-sub">{headerSub}</div>
              </div>
            </div>
            <div className="chat-header-actions">
              <button type="button" className="chat-icon-btn" onClick={ouvrirListeUsers} title="Messages privés">
                <Lock size={14} />
              </button>
              {canal !== 'public' && (
                <button type="button" className="chat-icon-btn" onClick={() => changerCanal('public')} title="Canal public">
                  <Users size={14} />
                </button>
              )}
              <button type="button" className="chat-icon-btn" onClick={() => setOuvert(false)} aria-label="Fermer">
                <X size={14} />
              </button>
            </div>
          </div>

          {vue === 'users' && (
            <div className="chat-users-list">
              <div className="chat-users-label">Choisir un destinataire</div>
              {utilisateurs.length === 0 ? (
                <p className="chat-empty">Aucun autre utilisateur actif.</p>
              ) : utilisateurs.map(u => {
                const nb = nonLusParPeer[u.id] || 0;
                return (
                  <button
                    key={u.id}
                    type="button"
                    className={`chat-user-row${canal !== 'public' && canal.id === u.id ? ' active' : ''}`}
                    onClick={() => changerCanal(u)}
                  >
                    <div className="chat-avatar" style={{ borderColor: getRoleColor(u.role), color: getRoleColor(u.role) }}>
                      {(u.fullname || u.username).charAt(0).toUpperCase()}
                    </div>
                    <div className="chat-user-info">
                      <span className="chat-user-name">{u.fullname || u.username}</span>
                      <RoleTag role={u.role} />
                    </div>
                    {nb > 0 && <span className="chat-peer-badge">{nb > 9 ? '9+' : nb}</span>}
                  </button>
                );
              })}
              <button type="button" className="chat-back-link" onClick={() => setVue('canal')}>
                ← Retour au canal
              </button>
            </div>
          )}

          {vue === 'canal' && (
            <>
              <div className="chat-messages">
                {messages.length === 0 && (
                  <div className="chat-empty">
                    <MessageSquare size={26} />
                    <p>{canal === 'public' ? 'Aucun message.' : 'Commencez la conversation.'}</p>
                  </div>
                )}
                {messages.map((msg, idx) => {
                  const estMoi = estMonMessage(msg, userId, username);
                  const color = getRoleColor(msg.auteur_role);
                  return (
                    <div key={msg.id || idx} className={`chat-bubble-row${estMoi ? ' mine' : ''}`}>
                      {!estMoi && (
                        <div className="chat-avatar small" style={{ borderColor: color, color }}>
                          {(msg.auteur_nom || '?').charAt(0).toUpperCase()}
                        </div>
                      )}
                      <div className="chat-bubble-wrap">
                        {!estMoi && (
                          <div className="chat-bubble-meta">
                            <span style={{ color }}>{msg.auteur_nom}</span>
                            <RoleTag role={msg.auteur_role} />
                          </div>
                        )}
                        <div className={`chat-bubble${estMoi ? ' mine' : ''}`}>{msg.contenu}</div>
                        <div className="chat-bubble-time">
                          {formatDateTimeTN(msg.date_envoi)}
                        </div>
                      </div>
                    </div>
                  );
                })}
                <div ref={bottomRef} />
              </div>

              {erreurEnvoi && (
                <div className="chat-error" role="alert">{erreurEnvoi}</div>
              )}

              <form className="chat-form" onSubmit={envoyerMessage}>
                <input
                  ref={inputRef}
                  value={saisie}
                  onChange={e => { setSaisie(e.target.value); if (erreurEnvoi) setErreurEnvoi(''); }}
                  placeholder={canal === 'public' ? 'Message au canal public…' : `Message à ${canal.username || ''}…`}
                  maxLength={500}
                  className="chat-input"
                />
                <button type="submit" className="chat-send-btn" disabled={!saisie.trim() || envoi} aria-label="Envoyer">
                  <Send size={14} />
                </button>
              </form>
            </>
          )}
        </div>
      )}
    </>
  );
}
