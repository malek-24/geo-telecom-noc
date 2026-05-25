import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { useAuth } from '../auth/AuthContext';
import Sidebar from '../components/Sidebar';
import { API_BASE_URL } from '../services/apiConfig';
import { DATA_REFRESH_MS } from '../dataRefreshMs';
import {
  Users, Settings, Activity, AlertTriangle, Edit, Trash2,
  Shield, ShieldAlert, Plus, Save, Activity as ActivityIcon,
  UserX, UserCheck, Lock, MessageSquare, Check, X,
  Radio, Thermometer, Cpu, Signal, Clock, Wifi
} from 'lucide-react';
import '../styles/AdminStyles.css';

export default function AdministrationPage() {
  const { token, role } = useAuth();
  const [activeTab, setActiveTab] = useState('users');

  const [users, setUsers] = useState([]);
  const [pendingComments, setPendingComments] = useState([]);
  const [settings, setSettings] = useState({});
  const [stats, setStats] = useState(null);

  // ── État pour l'onglet Antennes ──────────────────────────────
  const [antennes, setAntennes] = useState([]);
  const [antennesLoading, setAntennesLoading] = useState(false);
  const [antenneSearch, setAntenneSearch] = useState('');

  // Modal de modification des métriques
  const [isMetriquesModalOpen, setIsMetriquesModalOpen] = useState(false);
  const [antenneSelectionnee, setAntenneSelectionnee] = useState(null);
  const [metriquesForm, setMetriquesForm] = useState({
    temperature: '', cpu: '', signal: '', latence: '', disponibilite: ''
  });
  const [metriquesLoading, setMetriquesLoading] = useState(false);
  const [metriquesResultat, setMetriquesResultat] = useState(null); // Résultat IA après modif
  // ──────────────────────────────────────────────────────────────

  const [searchTerm, setSearchTerm] = useState('');
  const [roleFilter, setRoleFilter] = useState('');

  const [isUserModalOpen, setIsUserModalOpen] = useState(false);
  const [editingUser, setEditingUser] = useState(null);
  const [userFormData, setUserFormData] = useState({
    username: '', nom: '', email: '', role: 'ingenieur',
    departement: '', telephone: '', statut: 'Actif', password: ''
  });

  useEffect(() => {
    if (role === 'administrateur') {
      fetchData();
      const interval = setInterval(() => {
        if (activeTab === 'comments') fetchComments();
        if (activeTab === 'antennes') fetchAntennes();
      }, DATA_REFRESH_MS);
      return () => clearInterval(interval);
    }
  }, [role, activeTab]);

  const fetchData = async () => {
    fetchUsers();
    fetchComments();
    fetchSettings();
    try {
      const res = await axios.get(`${API_BASE_URL}/stats`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setStats(res.data);
    } catch (e) { console.error(e); }
  };

  const fetchUsers = async () => {
    try {
      const res = await axios.get(`${API_BASE_URL}/admin/users`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setUsers(res.data);
    } catch (e) { console.error(e); }
  };

  // ── Chargement des antennes ──────────────────────────────────
  const fetchAntennes = useCallback(async () => {
    setAntennesLoading(true);
    try {
      const res = await axios.get(`${API_BASE_URL}/antennes`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setAntennes(res.data);
    } catch (e) {
      console.error(e);
    } finally {
      setAntennesLoading(false);
    }
  }, [token]);

  useEffect(() => {
    if (activeTab === 'antennes' && role === 'administrateur') {
      fetchAntennes();
    }
  }, [activeTab, fetchAntennes, role]);

  // ── Ouvrir le modal de modification des métriques ────────────
  const ouvrirModalMetriques = (antenne) => {
    setAntenneSelectionnee(antenne);
    setMetriquesForm({
      temperature:   String(antenne.temperature   ?? ''),
      cpu:           String(antenne.cpu           ?? ''),
      signal:        String(antenne.signal        ?? ''),
      latence:       String(antenne.latence       ?? ''),
      disponibilite: String(antenne.disponibilite ?? ''),
    });
    setMetriquesResultat(null);
    setIsMetriquesModalOpen(true);
  };

  // ── Soumettre les nouvelles métriques ────────────────────────
  const handleSauvegarderMetriques = async () => {
    if (!antenneSelectionnee) return;
    setMetriquesLoading(true);
    setMetriquesResultat(null);

    try {
      const res = await axios.put(
        `${API_BASE_URL}/antennes/${antenneSelectionnee.id}/metriques`,
        {
          temperature:   parseFloat(metriquesForm.temperature),
          cpu:           parseFloat(metriquesForm.cpu),
          signal:        parseFloat(metriquesForm.signal),
          latence:       parseFloat(metriquesForm.latence),
          disponibilite: parseFloat(metriquesForm.disponibilite),
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      // Afficher le résultat de l'IA immédiatement
      setMetriquesResultat({
        success:    true,
        statut:     res.data.statut     || 'en calcul...',
        risk_score: res.data.risk_score ?? null,
        message:    res.data.message    || 'Métriques mises à jour.',
      });

      // Rafraîchir le tableau des antennes pour voir le nouveau statut
      fetchAntennes();

    } catch (e) {
      console.error(e);
      setMetriquesResultat({
        success: false,
        message: e.response?.data?.error || 'Erreur lors de la mise à jour.',
      });
    } finally {
      setMetriquesLoading(false);
    }
  };

  // ── Couleur selon le statut IA ───────────────────────────────
  const getStatutColor = (statut) => {
    switch (statut) {
      case 'critique': return '#ef4444';
      case 'alerte':   return '#f59e0b';
      case 'normal':   return '#22c55e';
      default:         return '#6b7280';
    }
  };

  const getStatutLabel = (statut) => {
    switch (statut) {
      case 'critique': return '🔴 Critique';
      case 'alerte':   return '🟡 Alerte';
      case 'normal':   return '🟢 Normal';
      default:         return '⚪ Inconnu';
    }
  };
  // ──────────────────────────────────────────────────────────────

  const fetchComments = async () => {
    try {
      const res = await axios.get(`${API_BASE_URL}/admin/commentaires`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setPendingComments(res.data);
    } catch (e) { console.error(e); }
  };

  const handleValidateComment = async (id) => {
    try {
      await axios.put(`${API_BASE_URL}/commentaires/${id}/valider`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      fetchComments();
    } catch (e) { console.error(e); }
  };

  const handleDeleteComment = async (id) => {
    if (!window.confirm("Êtes-vous sûr de vouloir supprimer ce commentaire ?")) return;
    try {
      await axios.delete(`${API_BASE_URL}/commentaires/${id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      fetchComments();
    } catch (e) { console.error(e); }
  };

  const fetchSettings = async () => {
    try {
      const res = await axios.get(`${API_BASE_URL}/admin/settings`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSettings(res.data);
    } catch (e) { console.error(e); }
  };

  const handleSaveUser = async () => {
    try {
      if (editingUser) {
        await axios.put(`${API_BASE_URL}/admin/users/${editingUser.id}`, userFormData, {
          headers: { Authorization: `Bearer ${token}` }
        });
      } else {
        await axios.post(`${API_BASE_URL}/admin/users`, userFormData, {
          headers: { Authorization: `Bearer ${token}` }
        });
      }
      setIsUserModalOpen(false);
      fetchUsers();
    } catch (e) { console.error(e); }
  };

  const handleDeleteUser = async (id) => {
    if (window.confirm("Êtes-vous sûr de vouloir supprimer cet utilisateur définitivement ?")) {
      try {
        await axios.delete(`${API_BASE_URL}/admin/users/${id}`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        fetchUsers();
      } catch (e) { console.error(e); }
    }
  };

  const handleToggleStatus = async (user) => {
    const newStatus = user.statut === 'Actif' ? 'Désactivé' : 'Actif';
    try {
      await axios.put(`${API_BASE_URL}/admin/users/${user.id}`, { statut: newStatus }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      fetchUsers();
    } catch (e) { console.error(e); }
  };

  const openUserModal = (user = null) => {
    if (user) {
      setEditingUser(user);
      setUserFormData({
        username: user.username || '',
        nom: user.nom || '',
        email: user.email || '',
        role: user.role || 'ingenieur_reseau',
        departement: user.departement || '',
        telephone: user.telephone || '',
        statut: user.statut || 'Actif',
        password: ''
      });
    } else {
      setEditingUser(null);
      setUserFormData({
        username: '', nom: '', email: '', role: 'ingenieur_reseau',
        departement: '', telephone: '', statut: 'Actif', password: ''
      });
    }
    setIsUserModalOpen(true);
  };

  const getRoleBadgeClass = (roleName) => {
    switch (roleName) {
      case 'administrateur':    return 'badge-admin';
      case 'ingenieur_reseau':  return 'badge-mod';
      case 'technicien_terrain': return 'badge-tech';
      default:                  return 'badge-obs';
    }
  };

  const filteredUsers = users.filter(u => {
    const matchSearch =
      (u.nom || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
      (u.email || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
      (u.username || '').toLowerCase().includes(searchTerm.toLowerCase());
    const matchRole = roleFilter ? u.role === roleFilter : true;
    return matchSearch && matchRole;
  });

  // Filtrage des antennes par nom ou zone
  const antennesFiltrees = antennes.filter(a =>
    (a.nom  || '').toLowerCase().includes(antenneSearch.toLowerCase()) ||
    (a.zone || '').toLowerCase().includes(antenneSearch.toLowerCase())
  );

  const handleSaveSettings = async () => {
    try {
      await axios.post(`${API_BASE_URL}/admin/settings`, settings, {
        headers: { Authorization: `Bearer ${token}` }
      });
      alert("Configuration sauvegardée !");
    } catch (e) { console.error(e); }
  };

  if (role !== 'administrateur') {
    return (
      <div className="admin-container">
        <Sidebar />
        <div className="admin-main" style={{ paddingTop: '20px' }}>
          <div className="admin-panel" style={{ textAlign: 'center', marginTop: '50px' }}>
            <ShieldAlert size={64} color="#ef4444" style={{ marginBottom: '20px' }} />
            <h2>Accès Interdit</h2>
            <p>Cette page est strictement réservée aux administrateurs du NOC.</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="admin-container">
      <Sidebar />
      <div className="admin-main" style={{ paddingTop: '20px' }}>

        <div className="admin-header">
          <h1>Centre de Contrôle Administrateur</h1>
          <p>Gestion globale du système GEO-TÉLÉCOM, sécurité, paramètres et maintien en condition opérationnelle.</p>
        </div>

        {/* ── ONGLETS ─────────────────────────────────────────── */}
        <div className="admin-tabs">
          <button
            className={`admin-tab ${activeTab === 'users' ? 'active' : ''}`}
            onClick={() => setActiveTab('users')}
          >
            <Users size={18} /> Utilisateurs
          </button>
          <button
            className={`admin-tab ${activeTab === 'antennes' ? 'active' : ''}`}
            onClick={() => setActiveTab('antennes')}
          >
            <Radio size={18} /> Antennes
          </button>
          <button
            className={`admin-tab ${activeTab === 'comments' ? 'active' : ''}`}
            onClick={() => setActiveTab('comments')}
          >
            <MessageSquare size={18} /> Validation Commentaires
          </button>
          <button
            className={`admin-tab ${activeTab === 'settings' ? 'active' : ''}`}
            onClick={() => setActiveTab('settings')}
          >
            <Settings size={18} /> Paramètres
          </button>
        </div>

        {/* ── ONGLET UTILISATEURS ────────────────────────────── */}
        {activeTab === 'users' && (
          <div>
            <div className="admin-kpi-grid">
              <div className="admin-kpi-card">
                <Users size={28} color="#60a5fa" />
                <div className="value">{users.filter(u => u.statut === 'Actif').length}</div>
                <div className="title">Utilisateurs Actifs</div>
              </div>
              <div className="admin-kpi-card">
                <ActivityIcon size={28} color="#34d399" />
                <div className="value">{users.filter(u => u.role === 'technicien_terrain').length}</div>
                <div className="title">Techniciens</div>
              </div>
              <div className="admin-kpi-card">
                <Shield size={28} color="#c084fc" />
                <div className="value">{users.filter(u => u.role === 'ingenieur_reseau').length}</div>
                <div className="title">Ingénieurs</div>
              </div>
              <div className="admin-kpi-card">
                <UserX size={28} color="#f87171" />
                <div className="value">{users.filter(u => u.statut === 'Désactivé' || u.statut === 'Inactif').length}</div>
                <div className="title">Comptes Désactivés</div>
              </div>
            </div>

            <div className="admin-panel">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                <h3>Gestion des Comptes Utilisateurs</h3>
                <button className="admin-btn success" onClick={() => openUserModal()}>
                  <Plus size={16} /> Ajouter utilisateur
                </button>
              </div>

              <div className="admin-search-bar">
                <div style={{ position: 'relative', flex: 1, maxWidth: '400px' }}>
                  <input
                    type="text"
                    placeholder="🔍 Rechercher par nom, email ou identifiant..."
                    className="admin-input"
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                  />
                </div>
                <select
                  className="admin-input"
                  style={{ maxWidth: '200px' }}
                  value={roleFilter}
                  onChange={(e) => setRoleFilter(e.target.value)}
                >
                  <option value="">Tous les rôles</option>
                  <option value="administrateur">Administrateur</option>
                  <option value="ingenieur_reseau">Ingénieur</option>
                  <option value="technicien_terrain">Technicien</option>
                </select>
              </div>

              <table className="admin-table">
                <thead>
                  <tr>
                    <th>Nom & Email</th>
                    <th>Identifiant</th>
                    <th>Rôle</th>
                    <th>Statut</th>
                    <th>Dernière Connexion</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredUsers.map(u => (
                    <tr key={u.id}>
                      <td>
                        <div><strong>{u.nom}</strong></div>
                        <div style={{ fontSize: '0.8rem', color: '#9ca3af' }}>{u.email}</div>
                      </td>
                      <td>{u.username}</td>
                      <td>
                        <span className={`admin-badge ${getRoleBadgeClass(u.role)}`}>
                          {u.role.toUpperCase()}
                        </span>
                      </td>
                      <td>
                        <span className={`admin-badge ${u.statut === 'Actif' ? 'badge-green' : 'badge-red'}`}>
                          {u.statut === 'Actif' ? '🟢 Actif' : '🔴 Désactivé'}
                        </span>
                      </td>
                      <td style={{ fontSize: '0.9rem', color: '#ccc' }}>{u.derniere_connexion}</td>
                      <td>
                        <button className="admin-btn ghost" title="Modifier" style={{ padding: '6px', marginRight: '5px' }} onClick={() => openUserModal(u)}>
                          <Edit size={16} color="#60a5fa" />
                        </button>
                        <button className="admin-btn ghost" title={u.statut === 'Actif' ? "Désactiver" : "Réactiver"} style={{ padding: '6px', marginRight: '5px' }} onClick={() => handleToggleStatus(u)}>
                          {u.statut === 'Actif' ? <UserX size={16} color="#fbbf24" /> : <UserCheck size={16} color="#34d399" />}
                        </button>
                        <button className="admin-btn ghost" title="Réinitialiser mot de passe" style={{ padding: '6px', marginRight: '5px' }} onClick={() => openUserModal(u)}>
                          <Lock size={16} color="#c084fc" />
                        </button>
                        <button className="admin-btn ghost" title="Supprimer" style={{ padding: '6px' }} onClick={() => handleDeleteUser(u.id)}>
                          <Trash2 size={16} color="#f87171" />
                        </button>
                      </td>
                    </tr>
                  ))}
                  {filteredUsers.length === 0 && (
                    <tr>
                      <td colSpan="6" style={{ textAlign: 'center', padding: '30px', color: '#9ca3af' }}>
                        Aucun utilisateur trouvé.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* ── ONGLET ANTENNES ────────────────────────────────── */}
        {activeTab === 'antennes' && (
          <div>
            {/* KPI rapides */}
            <div className="admin-kpi-grid">
              <div className="admin-kpi-card">
                <Radio size={28} color="#60a5fa" />
                <div className="value">{antennes.length}</div>
                <div className="title">Total Antennes</div>
              </div>
              <div className="admin-kpi-card">
                <Check size={28} color="#22c55e" />
                <div className="value">{antennes.filter(a => a.statut === 'normal').length}</div>
                <div className="title">Normales</div>
              </div>
              <div className="admin-kpi-card">
                <AlertTriangle size={28} color="#f59e0b" />
                <div className="value">{antennes.filter(a => a.statut === 'alerte').length}</div>
                <div className="title">En Alerte</div>
              </div>
              <div className="admin-kpi-card">
                <ShieldAlert size={28} color="#ef4444" />
                <div className="value">{antennes.filter(a => a.statut === 'critique').length}</div>
                <div className="title">Critiques</div>
              </div>
            </div>

            <div className="admin-panel">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                <h3><Radio size={20} style={{ marginRight: 8 }} />Modification Manuelle des Métriques</h3>
                <button className="admin-btn ghost" onClick={fetchAntennes} title="Rafraîchir">
                  ↻ Actualiser
                </button>
              </div>

              <p style={{ color: '#9ca3af', marginBottom: '16px', fontSize: '0.9rem' }}>
                Sélectionnez une antenne et modifiez ses métriques. L'IA recalculera
                instantanément le score de santé, l'état et les alertes.
              </p>

              {/* Barre de recherche antennes */}
              <div style={{ marginBottom: '16px' }}>
                <input
                  type="text"
                  placeholder="🔍 Rechercher une antenne par nom ou zone..."
                  className="admin-input"
                  style={{ maxWidth: '400px' }}
                  value={antenneSearch}
                  onChange={(e) => setAntenneSearch(e.target.value)}
                />
              </div>

              {antennesLoading ? (
                <div style={{ textAlign: 'center', padding: '40px', color: '#9ca3af' }}>
                  Chargement des antennes...
                </div>
              ) : (
                <div style={{ overflowX: 'auto' }}>
                  <table className="admin-table">
                    <thead>
                      <tr>
                        <th>Antenne</th>
                        <th>Zone</th>
                        <th>
                          <Thermometer size={14} style={{ marginRight: 4 }} />
                          Temp (°C)
                        </th>
                        <th>
                          <Cpu size={14} style={{ marginRight: 4 }} />
                          CPU (%)
                        </th>
                        <th>
                          <Signal size={14} style={{ marginRight: 4 }} />
                          Signal (dBm)
                        </th>
                        <th>
                          <Clock size={14} style={{ marginRight: 4 }} />
                          Latence (ms)
                        </th>
                        <th>
                          <Wifi size={14} style={{ marginRight: 4 }} />
                          Dispo (%)
                        </th>
                        <th>État IA</th>
                        <th>Action</th>
                      </tr>
                    </thead>
                    <tbody>
                      {antennesFiltrees.map(a => (
                        <tr key={a.id}>
                          <td>
                            <div><strong>{a.nom}</strong></div>
                            <div style={{ fontSize: '0.75rem', color: '#6b7280' }}>ID: {a.id}</div>
                          </td>
                          <td style={{ fontSize: '0.9rem' }}>{a.zone}</td>
                          <td style={{ fontFamily: 'monospace' }}>
                            {a.temperature != null ? Number(a.temperature).toFixed(1) : '—'}
                          </td>
                          <td style={{ fontFamily: 'monospace' }}>
                            {a.cpu != null ? Number(a.cpu).toFixed(1) : '—'}
                          </td>
                          <td style={{ fontFamily: 'monospace' }}>
                            {a.signal != null ? Number(a.signal).toFixed(1) : '—'}
                          </td>
                          <td style={{ fontFamily: 'monospace' }}>
                            {a.latence != null ? Number(a.latence).toFixed(1) : '—'}
                          </td>
                          <td style={{ fontFamily: 'monospace' }}>
                            {a.disponibilite != null ? Number(a.disponibilite).toFixed(1) : '—'}
                          </td>
                          <td>
                            <span style={{
                              color: getStatutColor(a.statut),
                              fontWeight: 600,
                              fontSize: '0.85rem'
                            }}>
                              {getStatutLabel(a.statut)}
                            </span>
                            {a.risk_score != null && (
                              <div style={{ fontSize: '0.75rem', color: '#6b7280' }}>
                                Risque: {Number(a.risk_score).toFixed(0)}%
                              </div>
                            )}
                          </td>
                          <td>
                            <button
                              className="admin-btn"
                              style={{ padding: '6px 12px', fontSize: '0.8rem' }}
                              onClick={() => ouvrirModalMetriques(a)}
                              title="Modifier les métriques"
                            >
                              <Edit size={14} /> Modifier
                            </button>
                          </td>
                        </tr>
                      ))}
                      {antennesFiltrees.length === 0 && (
                        <tr>
                          <td colSpan="9" style={{ textAlign: 'center', padding: '30px', color: '#9ca3af' }}>
                            Aucune antenne trouvée.
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        )}

        {/* ── ONGLET COMMENTAIRES ───────────────────────────── */}
        {activeTab === 'comments' && (
          <div className="admin-panel">
            <h3><MessageSquare size={20} /> Validation des Commentaires</h3>
            <p style={{ color: '#9ca3af', marginBottom: '20px' }}>
              Modération des commentaires techniques ajoutés par les techniciens et modérateurs.
            </p>
            {pendingComments.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
                <Check size={48} style={{ opacity: 0.2, marginBottom: '16px' }} />
                <p>Aucun commentaire en attente de validation.</p>
              </div>
            ) : (
              <table className="admin-table">
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Incident</th>
                    <th>Utilisateur</th>
                    <th>Rôle</th>
                    <th>Commentaire</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {pendingComments.map(c => (
                    <tr key={c.id}>
                      <td>{c.date_creation}</td>
                      <td><strong>{c.incident_titre || `Incident #${c.incident_id}`}</strong></td>
                      <td>{c.utilisateur_nom}</td>
                      <td><span className="admin-badge badge-blue">{c.role}</span></td>
                      <td style={{ maxWidth: '300px', whiteSpace: 'normal' }}>"{c.contenu}"</td>
                      <td>
                        <div style={{ display: 'flex', gap: '8px' }}>
                          <button className="admin-btn success" style={{ padding: '6px' }} onClick={() => handleValidateComment(c.id)} title="Valider">
                            <Check size={16} />
                          </button>
                          <button className="admin-btn danger" style={{ padding: '6px' }} onClick={() => handleDeleteComment(c.id)} title="Refuser / Supprimer">
                            <X size={16} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        )}

        {/* ── ONGLET PARAMÈTRES ─────────────────────────────── */}
        {activeTab === 'settings' && (
          <div className="admin-panel">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
              <h3>Configuration Système</h3>
              <button className="admin-btn" onClick={handleSaveSettings}>
                <Save size={16} /> Sauvegarder
              </button>
            </div>

            <div className="settings-grid">
              <div className="setting-item">
                <div>
                  <label>Fréquence de rafraîchissement des mesures (secondes)</label>
                  <div className="setting-desc">Temps d'attente entre deux appels à l'API stats.</div>
                </div>
                <input type="number" className="admin-input" style={{ width: '80px' }}
                  value={settings.update_freq || 5}
                  onChange={e => setSettings({ ...settings, update_freq: parseInt(e.target.value) })}
                />
              </div>

              <div className="setting-item">
                <div>
                  <label>Seuil d'alerte Température extérieure (°C)</label>
                  <div className="setting-desc">Déclenche une alerte orange si dépassé. (Normal : &lt; 40°C)</div>
                </div>
                <input type="number" className="admin-input" style={{ width: '80px' }}
                  value={settings.temp_threshold || 40}
                  onChange={e => setSettings({ ...settings, temp_threshold: parseInt(e.target.value) })}
                />
              </div>

              <div className="setting-item">
                <div>
                  <label>Seuil d'alerte CPU (%)</label>
                  <div className="setting-desc">Déclenche une alerte jaune si dépassé.</div>
                </div>
                <input type="number" className="admin-input" style={{ width: '80px' }}
                  value={settings.cpu_threshold || 85}
                  onChange={e => setSettings({ ...settings, cpu_threshold: parseInt(e.target.value) })}
                />
              </div>

              <div className="setting-item">
                <div>
                  <label>Activation Analyse IA (IsolationForest)</label>
                  <div className="setting-desc">Active ou désactive la détection d'anomalies en temps réel.</div>
                </div>
                <select className="admin-input" style={{ width: '120px' }}
                  value={settings.ia_active ? "true" : "false"}
                  onChange={e => setSettings({ ...settings, ia_active: e.target.value === "true" })}
                >
                  <option value="true">Activé</option>
                  <option value="false">Désactivé</option>
                </select>
              </div>

              <div className="setting-item" style={{ borderLeft: '4px solid #ef4444' }}>
                <div>
                  <label style={{ color: '#ef4444' }}>Mode Maintenance Globale</label>
                  <div className="setting-desc">Désactive l'accès aux utilisateurs non-admin.</div>
                </div>
                <select className="admin-input" style={{ width: '120px', borderColor: '#ef4444' }}
                  value={settings.maintenance_mode ? "true" : "false"}
                  onChange={e => setSettings({ ...settings, maintenance_mode: e.target.value === "true" })}
                >
                  <option value="false">Off</option>
                  <option value="true">On</option>
                </select>
              </div>
            </div>
          </div>
        )}


        {/* ── MODAL MODIFICATION MÉTRIQUES ─────────────────── */}
        {isMetriquesModalOpen && antenneSelectionnee && (
          <div className="admin-modal-overlay">
            <div className="admin-modal" style={{ width: '560px' }}>

              {/* Titre du modal */}
              <div style={{ marginBottom: '20px' }}>
                <h3 style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <Edit size={20} color="#60a5fa" />
                  Modification des métriques — {antenneSelectionnee.nom}
                </h3>
                <div style={{ fontSize: '0.85rem', color: '#9ca3af', marginTop: 4 }}>
                  Zone : {antenneSelectionnee.zone} &nbsp;|&nbsp; ID : {antenneSelectionnee.id}
                </div>
              </div>

              {/* Info pédagogique */}
              <div style={{
                background: 'rgba(96, 165, 250, 0.1)',
                border: '1px solid rgba(96, 165, 250, 0.3)',
                borderRadius: 8,
                padding: '10px 14px',
                marginBottom: 20,
                fontSize: '0.85rem',
                color: '#93c5fd'
              }}>
                ℹ️ Après validation, l'IA Isolation Forest recalculera immédiatement le score
                de santé, l'état et les alertes pour cette antenne.
              </div>

              {/* Formulaire des 5 métriques */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>

                <div className="form-group">
                  <label style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    <Thermometer size={14} color="#f87171" />
                    Température extérieure (°C)
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    className="admin-input"
                    value={metriquesForm.temperature}
                    onChange={e => setMetriquesForm({ ...metriquesForm, temperature: e.target.value })}
                    placeholder="ex: 42.0"
                  />
                  <div style={{ fontSize: '0.75rem', color: '#6b7280', marginTop: 4 }}>
                    Normal &lt; 40°C · Alerte 40-45°C · Critique &gt; 45°C
                  </div>
                </div>

                <div className="form-group">
                  <label style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    <Cpu size={14} color="#a78bfa" />
                    Charge CPU (%)
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    min="0"
                    max="100"
                    className="admin-input"
                    value={metriquesForm.cpu}
                    onChange={e => setMetriquesForm({ ...metriquesForm, cpu: e.target.value })}
                    placeholder="ex: 85.0"
                  />
                  <div style={{ fontSize: '0.75rem', color: '#6b7280', marginTop: 4 }}>
                    Normal &lt; 60% · Alerte si &gt; 80%
                  </div>
                </div>

                <div className="form-group">
                  <label style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    <Signal size={14} color="#34d399" />
                    Signal RSSI (dBm)
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    className="admin-input"
                    value={metriquesForm.signal}
                    onChange={e => setMetriquesForm({ ...metriquesForm, signal: e.target.value })}
                    placeholder="ex: -90.0"
                  />
                  <div style={{ fontSize: '0.75rem', color: '#6b7280', marginTop: 4 }}>
                    Bon : -70 à -50 · Faible &lt; -95
                  </div>
                </div>

                <div className="form-group">
                  <label style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    <Clock size={14} color="#fbbf24" />
                    Latence réseau (ms)
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    min="0"
                    className="admin-input"
                    value={metriquesForm.latence}
                    onChange={e => setMetriquesForm({ ...metriquesForm, latence: e.target.value })}
                    placeholder="ex: 150.0"
                  />
                  <div style={{ fontSize: '0.75rem', color: '#6b7280', marginTop: 4 }}>
                    Normal &lt; 50ms · Élevée &gt; 100ms
                  </div>
                </div>

                <div className="form-group" style={{ gridColumn: '1 / -1' }}>
                  <label style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    <Wifi size={14} color="#60a5fa" />
                    Disponibilité réseau (%)
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    min="0"
                    max="100"
                    className="admin-input"
                    style={{ maxWidth: '200px' }}
                    value={metriquesForm.disponibilite}
                    onChange={e => setMetriquesForm({ ...metriquesForm, disponibilite: e.target.value })}
                    placeholder="ex: 90.0"
                  />
                  <div style={{ fontSize: '0.75rem', color: '#6b7280', marginTop: 4 }}>
                    Normal ≥ 95% · Problème &lt; 90%
                  </div>
                </div>
              </div>

              {/* Résultat IA après validation */}
              {metriquesResultat && (
                <div style={{
                  marginTop: 20,
                  padding: '12px 16px',
                  borderRadius: 8,
                  background: metriquesResultat.success
                    ? 'rgba(34, 197, 94, 0.1)'
                    : 'rgba(239, 68, 68, 0.1)',
                  border: `1px solid ${metriquesResultat.success ? 'rgba(34, 197, 94, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`,
                }}>
                  {metriquesResultat.success ? (
                    <>
                      <div style={{ fontWeight: 600, color: '#22c55e', marginBottom: 6 }}>
                        ✅ Métriques mises à jour — IA recalculée
                      </div>
                      {metriquesResultat.statut && (
                        <div style={{ display: 'flex', gap: 20, fontSize: '0.9rem' }}>
                          <span>
                            État IA :&nbsp;
                            <strong style={{ color: getStatutColor(metriquesResultat.statut) }}>
                              {getStatutLabel(metriquesResultat.statut)}
                            </strong>
                          </span>
                          {metriquesResultat.risk_score != null && (
                            <span>
                              Score de risque :&nbsp;
                              <strong style={{ color: getStatutColor(metriquesResultat.statut) }}>
                                {Number(metriquesResultat.risk_score).toFixed(1)}%
                              </strong>
                            </span>
                          )}
                        </div>
                      )}
                    </>
                  ) : (
                    <div style={{ color: '#ef4444' }}>
                      ❌ {metriquesResultat.message}
                    </div>
                  )}
                </div>
              )}

              {/* Boutons du modal */}
              <div className="modal-actions" style={{ marginTop: '24px' }}>
                <button
                  className="admin-btn ghost"
                  onClick={() => { setIsMetriquesModalOpen(false); setMetriquesResultat(null); }}
                >
                  Fermer
                </button>
                <button
                  className="admin-btn success"
                  onClick={handleSauvegarderMetriques}
                  disabled={metriquesLoading}
                >
                  {metriquesLoading ? (
                    '⏳ Analyse IA en cours...'
                  ) : (
                    <><Save size={16} /> Valider &amp; Recalculer IA</>
                  )}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* ── MODAL UTILISATEUR ─────────────────────────────── */}
        {isUserModalOpen && (
          <div className="admin-modal-overlay">
            <div className="admin-modal" style={{ width: '600px' }}>
              <h3>{editingUser ? 'Modifier Utilisateur' : 'Ajouter Nouvel Utilisateur'}</h3>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px' }}>
                <div className="form-group">
                  <label>Nom complet *</label>
                  <input type="text" className="admin-input" value={userFormData.nom} onChange={e => setUserFormData({ ...userFormData, nom: e.target.value })} required />
                </div>
                <div className="form-group">
                  <label>Nom d'utilisateur (Login) *</label>
                  <input type="text" className="admin-input" value={userFormData.username} onChange={e => setUserFormData({ ...userFormData, username: e.target.value })} disabled={!!editingUser} required />
                </div>
                <div className="form-group">
                  <label>Email *</label>
                  <input type="email" className="admin-input" value={userFormData.email} onChange={e => setUserFormData({ ...userFormData, email: e.target.value })} required />
                </div>
                <div className="form-group">
                  <label>Mot de passe {editingUser && '(Laisser vide pour ne pas changer)'}</label>
                  <input type="password" className="admin-input" value={userFormData.password} onChange={e => setUserFormData({ ...userFormData, password: e.target.value })} />
                </div>
                <div className="form-group">
                  <label>Rôle *</label>
                  <select className="admin-input" value={userFormData.role} onChange={e => setUserFormData({ ...userFormData, role: e.target.value })}>
                    <option value="administrateur">Administrateur</option>
                    <option value="ingenieur_reseau">Ingénieur</option>
                    <option value="technicien_terrain">Technicien</option>
                  </select>
                </div>
                <div className="form-group">
                  <label>Statut *</label>
                  <select className="admin-input" value={userFormData.statut} onChange={e => setUserFormData({ ...userFormData, statut: e.target.value })}>
                    <option value="Actif">Actif</option>
                    <option value="Désactivé">Désactivé</option>
                  </select>
                </div>
                <div className="form-group">
                  <label>Département</label>
                  <input type="text" className="admin-input" value={userFormData.departement} onChange={e => setUserFormData({ ...userFormData, departement: e.target.value })} />
                </div>
                <div className="form-group">
                  <label>Téléphone</label>
                  <input type="tel" className="admin-input" value={userFormData.telephone} onChange={e => setUserFormData({ ...userFormData, telephone: e.target.value })} />
                </div>
              </div>

              <div className="modal-actions" style={{ marginTop: '30px' }}>
                <button className="admin-btn ghost" onClick={() => setIsUserModalOpen(false)}>Annuler</button>
                <button className="admin-btn success" onClick={handleSaveUser}>
                  {editingUser ? 'Enregistrer les modifications' : "Créer l'utilisateur"}
                </button>
              </div>
            </div>
          </div>
        )}

      </div>
    </div>
  );
}
