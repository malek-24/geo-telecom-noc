/*
 * ProtectedRoute.js  —  Protection des routes par authentification
 *
 * Ce composant est utilisé dans App.js pour envelopper chaque page
 * qui nécessite une connexion. Il vérifie 3 choses :
 *
 *   1. Est-ce que la session est en cours de vérification ? → Affiche un écran d'attente
 *   2. L'utilisateur est-il connecté ? → Sinon, redirige vers /login
 *   3. L'utilisateur a-t-il le bon rôle ? → Sinon, redirige vers /dashboard
 *
 * Utilisation dans App.js :
 *   <ProtectedRoute>                    → accessible à tous les connectés
 *   <ProtectedRoute roles={[ROLE.ADMIN]}> → accessible aux admins seulement
 */

import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { hasRole } from "../auth/roles";

export default function ProtectedRoute({ children, roles }) {
  // Récupérer les informations de session depuis le contexte
  const { estConnecte, loading, role } = useAuth();

  // Mémoriser la page que l'utilisateur voulait visiter
  // (pour le rediriger dessus après connexion)
  const location = useLocation();

  // ── Étape 1 : Vérification de la session en cours ──
  // Au démarrage, l'application vérifie si le token est valide.
  // Pendant cette vérification, on affiche un écran d'attente.
  if (loading) {
    return (
      <div className="login-screen">
        <div className="login-card">
          <p>Vérification de la session…</p>
        </div>
      </div>
    );
  }

  // ── Étape 2 : L'utilisateur n'est pas connecté ──
  // On le redirige vers /login en mémorisant la page demandée.
  if (!estConnecte) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // ── Étape 3 : Vérification du rôle (si requis) ──
  // Si la route exige un rôle spécifique et que l'utilisateur ne l'a pas,
  // on le redirige vers le dashboard (page accessible à tous).
  if (roles && !hasRole(role, roles)) {
    return <Navigate to="/dashboard" replace />;
  }

  // ── Accès autorisé : afficher la page demandée ──
  return children;
}
