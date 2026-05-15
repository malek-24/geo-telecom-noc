/*
 * AuthContext.js  —  Gestion de la session utilisateur
 *
 * Ce fichier crée un "contexte" React : une variable globale accessible
 * depuis n'importe quel composant de l'application.
 *
 * Il gère :
 *   - La connexion (login) : appel à l'API, sauvegarde du token
 *   - La déconnexion (logout) : effacement de la session
 *   - La vérification au démarrage : est-ce que le token est encore valide ?
 *
 * Utilisation dans un composant :
 *   const { username, role, login, logout, estConnecte } = useAuth();
 */

import React, { createContext, useContext, useState, useEffect } from "react";
import { API_BASE_URL } from "../services/apiConfig";

// =============================================================
// Clés de stockage dans le navigateur (localStorage)
// localStorage = mémoire persistante du navigateur
// =============================================================
const CLE_TOKEN = "geo_token";
const CLE_USERNAME = "geo_username";
const CLE_ROLE = "geo_role";

// Créer le contexte (sera rempli par AuthProvider)
const AuthContext = createContext(null);

// =============================================================
// AuthProvider — Composant enveloppe de toute l'application
// Il fournit les informations de session à tous les composants enfants.
// =============================================================
export function AuthProvider({ children }) {

  // Lire la session sauvegardée (si l'utilisateur avait déjà ouvert le site)
  const [token, setToken] = useState(localStorage.getItem(CLE_TOKEN));
  const [username, setUsername] = useState(localStorage.getItem(CLE_USERNAME));
  const [role, setRole] = useState(localStorage.getItem(CLE_ROLE));

  // Indicateur de chargement (pendant la vérification du token au démarrage)
  const [loading, setLoading] = useState(false);

  // =============================================================
  // VÉRIFICATION DU TOKEN AU DÉMARRAGE
  // Au chargement de l'application, on vérifie si le token
  // sauvegardé est encore valide (appel à /auth/me).
  // =============================================================
  useEffect(() => {
    // Si pas de token, l'utilisateur n'est pas connecté → rien à faire
    if (!token) return;

    setLoading(true);

    fetch(`${API_BASE_URL}/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((reponse) => {
        if (!reponse.ok) throw new Error("Token invalide");
        return reponse.json();
      })
      .then((donnees) => {
        // Mettre à jour les infos utilisateur depuis le serveur
        setUsername(donnees.username);
        setRole(donnees.role);
      })
      .catch(() => {
        // Token invalide ou expiré → effacer la session
        localStorage.removeItem(CLE_TOKEN);
        localStorage.removeItem(CLE_USERNAME);
        localStorage.removeItem(CLE_ROLE);
        setToken(null);
        setUsername(null);
        setRole(null);
      })
      .finally(() => {
        setLoading(false);
      });
  }, []); // [] = s'exécute UNE SEULE FOIS au démarrage de l'application

  // =============================================================
  // FONCTION : Connexion
  // Appelle l'API /auth/login avec identifiant + mot de passe.
  // En cas de succès, sauvegarde le token dans le navigateur.
  // =============================================================
  async function login(nomUtilisateur, motDePasse) {
    const reponse = await fetch(`${API_BASE_URL}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username: nomUtilisateur, password: motDePasse }),
    });

    const donnees = await reponse.json().catch(() => ({}));

    if (!reponse.ok) {
      throw new Error(donnees.error || "Connexion refusée");
    }

    // Sauvegarder dans localStorage (persistance entre sessions)
    localStorage.setItem(CLE_TOKEN, donnees.token);
    localStorage.setItem(CLE_USERNAME, donnees.username);
    localStorage.setItem(CLE_ROLE, donnees.role);

    // Mettre à jour l'état React (affichage immédiat)
    setToken(donnees.token);
    setUsername(donnees.username);
    setRole(donnees.role);

    return donnees;
  }

  // =============================================================
  // FONCTION : Déconnexion
  // Efface le token du navigateur et remet l'état à zéro.
  // =============================================================
  function logout() {
    localStorage.removeItem(CLE_TOKEN);
    localStorage.removeItem(CLE_USERNAME);
    localStorage.removeItem(CLE_ROLE);

    setToken(null);
    setUsername(null);
    setRole(null);
  }

  // =============================================================
  // Valeur partagée avec tous les composants enfants
  // =============================================================
  const valeurPartagee = {
    token,
    username,
    role,
    loading,
    login,
    logout,
    estConnecte: Boolean(token && role),  // true si l'utilisateur est connecté
  };

  return (
    <AuthContext.Provider value={valeurPartagee}>
      {children}
    </AuthContext.Provider>
  );
}

// =============================================================
// Hook personnalisé : useAuth()
// Permet d'accéder au contexte depuis n'importe quel composant.
// Exemple : const { username, logout } = useAuth();
// =============================================================
export function useAuth() {
  const contexte = useContext(AuthContext);
  if (!contexte) {
    throw new Error("useAuth() doit être utilisé à l'intérieur de <AuthProvider>");
  }
  return contexte;
}
