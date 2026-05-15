import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from '../auth/AuthContext';
import Sidebar from '../components/Sidebar';
import { API_BASE_URL } from '../services/apiConfig';
import { Users, Settings, Activity, AlertTriangle, Edit, Trash2, Shield, ShieldAlert, Plus, Save, Activity as ActivityIcon, UserX, UserCheck, Lock, MessageSquare, Check, X } from 'lucide-react';
import '../styles/AdminStyles.css';

export default function AdministrationPage() {
  const { token, role } = useAuth();
  const [activeTab, setActiveTab] = useState('users'); // Set default to users for easier access

  const [users, setUsers] = useState([]);
  const [pendingComments, setPendingComments] = useState([]);
  const [settings, setSettings] = useState({});
  const [stats, setStats] = useState(null);

  const [searchTerm, setSearchTerm] = useState('');
  const [roleFilter, setRoleFilter] = useState('');

  const [isUserModalOpen, setIsUserModalOpen] = useState(false);
  const [editingUser, setEditingUser] = useState(null);
  const [userFormData, setUserFormData] = useState({ username: '', nom: '', email: '', role: 'ingenieur', departement: '', telephone: '', statut: 'Actif', password: '' });

  useEffect(() => {
    if (role === 'administrateur') {
      fetchData();
      const interval = setInterval(() => {
        if (activeTab === 'comments') fetchComments();
      }, 30000); 
      return () => clearInterval(interval);
    }
  }, [role, activeTab]);

  const fetchData = async () => {
    fetchUsers();
    fetchComments();
    fetchSettings();
    try {
      const res = await axios.get(`${API_BASE_URL}/stats`, { headers: { Authorization: `Bearer ${token}` } });
      setStats(res.data);
    } catch (e) { console.error(e); }
  };

  const fetchUsers = async () => {
    try {
      const res = await axios.get(`${API_BASE_URL}/admin/users`, { headers: { Authorization: `Bearer ${token}` } });
      setUsers(res.data);
    } catch (e) { console.error(e); }
  };

  const fetchComments = async () => {
    try {
      const res = await axios.get(`${API_BASE_URL}/admin/commentaires`, { headers: { Authorization: `Bearer ${token}` } });
      setPendingComments(res.data);
    } catch (e) { console.error(e); }
  };

  const handleValidateComment = async (id) => {
    try {
      await axios.put(`${API_BASE_URL}/commentaires/${id}/valider`, {}, { headers: { Authorization: `Bearer ${token}` } });
      fetchComments();
    } catch (e) { console.error(e); }
  };

  const handleDeleteComment = async (id) => {
    if (!window.confirm("Êtes-vous sûr de vouloir supprimer ce commentaire ?")) return;
    try {
      await axios.delete(`${API_BASE_URL}/commentaires/${id}`, { headers: { Authorization: `Bearer ${token}` } });
      fetchComments();
    } catch (e) { console.error(e); }
  };

  const fetchSettings = async () => {
    try {
      const res = await axios.get(`${API_BASE_URL}/admin/settings`, { headers: { Authorization: `Bearer ${token}` } });
      setSettings(res.data);
    } catch (e) { console.error(e); }
  };

  // --- Users Handlers ---
  const handleSaveUser = async () => {
    try {
      if (editingUser) {
        await axios.put(`${API_BASE_URL}/admin/users/${editingUser.id}`, userFormData, { headers: { Authorization: `Bearer ${token}` } });
      } else {
        await axios.post(`${API_BASE_URL}/admin/users`, userFormData, { headers: { Authorization: `Bearer ${token}` } });
      }
      setIsUserModalOpen(false);
      fetchUsers();
    } catch (e) { console.error(e); }
  };

  const handleDeleteUser = async (id) => {
    if (window.confirm("Êtes-vous sûr de vouloir supprimer cet utilisateur définitivement ?")) {
      try {
        await axios.delete(`${API_BASE_URL}/admin/users/${id}`, { headers: { Authorization: `Bearer ${token}` } });
        fetchUsers();
      } catch (e) { console.error(e); }
    }
  };

  const handleToggleStatus = async (user) => {
    const newStatus = user.statut === 'Actif' ? 'Désactivé' : 'Actif';
    try {
      await axios.put(`${API_BASE_URL}/admin/users/${user.id}`, { statut: newStatus }, { headers: { Authorization: `Bearer ${token}` } });
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
      setUserFormData({ username: '', nom: '', email: '', role: 'ingenieur_reseau', departement: '', telephone: '', statut: 'Actif', password: '' });
    }
    setIsUserModalOpen(true);
  };

  const getRoleBadgeClass = (roleName) => {
    switch (roleName) {
      case 'administrateur': return 'badge-admin';
      case 'ingenieur_reseau': return 'badge-mod';
      case 'technicien_terrain': return 'badge-tech';
      default: return 'badge-obs';
    }
  };

  const filteredUsers = users.filter(u => {
    const matchSearch = (u.nom || '').toLowerCase().includes(searchTerm.toLowerCase()) || 
                        (u.email || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
                        (u.username || '').toLowerCase().includes(searchTerm.toLowerCase());
    const matchRole = roleFilter ? u.role === roleFilter : true;
    return matchSearch && matchRole;
  });

  // --- Settings Handlers ---
  const handleSaveSettings = async () => {
    try {
      await axios.post(`${API_BASE_URL}/admin/settings`, settings, { headers: { Authorization: `Bearer ${token}` } });
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

        <div className="admin-tabs">
          <button className={`admin-tab ${activeTab === 'users' ? 'active' : ''}`} onClick={() => setActiveTab('users')}><Users size={18} /> Utilisateurs</button>
          <button className={`admin-tab ${activeTab === 'comments' ? 'active' : ''}`} onClick={() => setActiveTab('comments')}><MessageSquare size={18} /> Validation Commentaires</button>
          <button className={`admin-tab ${activeTab === 'settings' ? 'active' : ''}`} onClick={() => setActiveTab('settings')}><Settings size={18} /> Paramètres</button>
        </div>

        {/* --- TAB USERS --- */}
        {activeTab === 'users' && (
          <div>
            {/* KPI Users */}
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
                <button className="admin-btn success" onClick={() => openUserModal()}><Plus size={16} /> Ajouter utilisateur</button>
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
                <select className="admin-input" style={{ maxWidth: '200px' }} value={roleFilter} onChange={(e) => setRoleFilter(e.target.value)}>
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

        {/* --- TAB COMMENTS --- */}
        {activeTab === 'comments' && (
          <div className="admin-panel">
            <h3><MessageSquare size={20} /> Validation des Commentaires</h3>
            <p style={{ color: '#9ca3af', marginBottom: '20px' }}>Modération des commentaires techniques ajoutés par les techniciens et modérateurs.</p>
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

        {/* --- TAB SETTINGS --- */}
        {activeTab === 'settings' && (
          <div className="admin-panel">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
              <h3>Configuration Système</h3>
              <button className="admin-btn" onClick={handleSaveSettings}><Save size={16} /> Sauvegarder</button>
            </div>

            <div className="settings-grid">
              <div className="setting-item">
                <div>
                  <label>Fréquence de rafraîchissement des mesures (secondes)</label>
                  <div className="setting-desc">Temps d'attente entre deux appels à l'API stats.</div>
                </div>
                <input type="number" className="admin-input" style={{ width: '80px' }} 
                  value={settings.update_freq || 5} 
                  onChange={e => setSettings({...settings, update_freq: parseInt(e.target.value)})} 
                />
              </div>

              <div className="setting-item">
                <div>
                  <label>Seuil d'alerte Température (°C)</label>
                  <div className="setting-desc">Déclenche une alerte orange si dépassé.</div>
                </div>
                <input type="number" className="admin-input" style={{ width: '80px' }} 
                  value={settings.temp_threshold || 75} 
                  onChange={e => setSettings({...settings, temp_threshold: parseInt(e.target.value)})} 
                />
              </div>

              <div className="setting-item">
                <div>
                  <label>Seuil d'alerte CPU (%)</label>
                  <div className="setting-desc">Déclenche une alerte jaune si dépassé.</div>
                </div>
                <input type="number" className="admin-input" style={{ width: '80px' }} 
                  value={settings.cpu_threshold || 85} 
                  onChange={e => setSettings({...settings, cpu_threshold: parseInt(e.target.value)})} 
                />
              </div>

              <div className="setting-item">
                <div>
                  <label>Activation Analyse IA (IsolationForest)</label>
                  <div className="setting-desc">Active ou désactive la détection d'anomalies en temps réel.</div>
                </div>
                <select className="admin-input" style={{ width: '120px' }} value={settings.ia_active ? "true" : "false"} onChange={e => setSettings({...settings, ia_active: e.target.value === "true"})}>
                  <option value="true">Activé</option>
                  <option value="false">Désactivé</option>
                </select>
              </div>

              <div className="setting-item" style={{ borderLeft: '4px solid #ef4444' }}>
                <div>
                  <label style={{ color: '#ef4444' }}>Mode Maintenance Globale</label>
                  <div className="setting-desc">Désactive l'accès aux utilisateurs non-admin.</div>
                </div>
                <select className="admin-input" style={{ width: '120px', borderColor: '#ef4444' }} value={settings.maintenance_mode ? "true" : "false"} onChange={e => setSettings({...settings, maintenance_mode: e.target.value === "true"})}>
                  <option value="false">Off</option>
                  <option value="true">On</option>
                </select>
              </div>
            </div>
          </div>
        )}



        {/* --- USER MODAL --- */}
        {isUserModalOpen && (
          <div className="admin-modal-overlay">
            <div className="admin-modal" style={{ width: '600px' }}>
              <h3>{editingUser ? 'Modifier Utilisateur' : 'Ajouter Nouvel Utilisateur'}</h3>
              
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px' }}>
                <div className="form-group">
                  <label>Nom complet *</label>
                  <input type="text" className="admin-input" value={userFormData.nom} onChange={e => setUserFormData({...userFormData, nom: e.target.value})} required />
                </div>
                <div className="form-group">
                  <label>Nom d'utilisateur (Login) *</label>
                  <input type="text" className="admin-input" value={userFormData.username} onChange={e => setUserFormData({...userFormData, username: e.target.value})} disabled={!!editingUser} required />
                </div>
                <div className="form-group">
                  <label>Email *</label>
                  <input type="email" className="admin-input" value={userFormData.email} onChange={e => setUserFormData({...userFormData, email: e.target.value})} required />
                </div>
                <div className="form-group">
                  <label>Mot de passe {editingUser && '(Laisser vide pour ne pas changer)'}</label>
                  <input type="password" className="admin-input" value={userFormData.password} onChange={e => setUserFormData({...userFormData, password: e.target.value})} />
                </div>
                <div className="form-group">
                  <label>Rôle *</label>
                  <select className="admin-input" value={userFormData.role} onChange={e => setUserFormData({...userFormData, role: e.target.value})}>
                    <option value="administrateur">Administrateur</option>
                    <option value="ingenieur_reseau">Ingénieur</option>
                    <option value="technicien_terrain">Technicien</option>
                  </select>
                </div>
                <div className="form-group">
                  <label>Statut *</label>
                  <select className="admin-input" value={userFormData.statut} onChange={e => setUserFormData({...userFormData, statut: e.target.value})}>
                    <option value="Actif">Actif</option>
                    <option value="Désactivé">Désactivé</option>
                  </select>
                </div>
                <div className="form-group">
                  <label>Département</label>
                  <input type="text" className="admin-input" value={userFormData.departement} onChange={e => setUserFormData({...userFormData, departement: e.target.value})} />
                </div>
                <div className="form-group">
                  <label>Téléphone</label>
                  <input type="tel" className="admin-input" value={userFormData.telephone} onChange={e => setUserFormData({...userFormData, telephone: e.target.value})} />
                </div>
              </div>
              
              <div className="modal-actions" style={{ marginTop: '30px' }}>
                <button className="admin-btn ghost" onClick={() => setIsUserModalOpen(false)}>Annuler</button>
                <button className="admin-btn success" onClick={handleSaveUser}>
                  {editingUser ? 'Enregistrer les modifications' : 'Créer l\'utilisateur'}
                </button>
              </div>
            </div>
          </div>
        )}

      </div>
    </div>
  );
}
