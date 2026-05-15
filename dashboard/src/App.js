/*
 * App.js  —  Point d'entrée de l'application React NOC v2.1
 *
 * Routes définies :
 *   /login                → page de connexion (accessible à tous)
 *   /dashboard            → tableau de bord principal (tous les rôles)
 *   /map                  → carte réseau interactive (tous les rôles)
 *   /equipments           → liste des antennes (tous les rôles)
 *   /moderation           → incidents & commentaires (admin, modérateur, technicien)
 *   /technicien/anomalies → alias → redirige vers /moderation
 *   /rapports             → rapports (admin, ingénieur, modérateur)
 *   /administration       → administration (admin seulement)
 *
 * Composants globaux injectés pour les utilisateurs connectés :
 *   - CriticalAlertBanner : popup temps réel quand antenne devient critique
 *   - ChatWidget          : mini chat interne flottant
 */

import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";

import LoginPage          from "./pages/Login";
import Dashboard          from "./pages/Dashboard";
import MapPage            from "./pages/NetworkMap";
import EquipmentsPage     from "./pages/Antennes";
import IncidentsPage      from "./pages/Incidents";
import RapportsPage       from "./pages/Reports";
import AdministrationPage from "./pages/Admin";
import AntennaHistoryPage from "./pages/AntenneHistory";

// ── Auth ──
import ProtectedRoute from "./components/ProtectedRoute";
import { ROLE }       from "./auth/roles";
import { useAuth }    from "./auth/AuthContext";

// ── Composants globaux ──
import CriticalAlertBanner from "./components/CriticalAlertBanner";
import ChatWidget          from "./components/ChatWidget";

/**
 * AppGlobal — wrapper qui injecte les composants globaux
 * uniquement quand l'utilisateur est connecté.
 */
function AppGlobal() {
  const { estConnecte } = useAuth();
  if (!estConnecte) return null;
  return (
    <>
      <CriticalAlertBanner />
      <ChatWidget />
    </>
  );
}

function App() {
  return (
    <Router>
      {/* Alertes critiques + chat actifs sur toutes les pages protégées */}
      <AppGlobal />

      <Routes>
        {/* Connexion */}
        <Route path="/login" element={<LoginPage />} />

        {/* Redirection racine → dashboard */}
        <Route path="/" element={<Navigate to="/dashboard" replace />} />

        {/* ── Pages accessibles à tous les rôles connectés ── */}
        <Route
          path="/dashboard"
          element={<ProtectedRoute><Dashboard /></ProtectedRoute>}
        />
        <Route
          path="/map"
          element={<ProtectedRoute><MapPage /></ProtectedRoute>}
        />
        <Route
          path="/equipments"
          element={<ProtectedRoute><EquipmentsPage /></ProtectedRoute>}
        />
        <Route
          path="/antenne/:id/history"
          element={<ProtectedRoute><AntennaHistoryPage /></ProtectedRoute>}
        />

        {/* Rapports — Admin, Ingénieur, Ingénieur */}
        <Route
          path="/rapports"
          element={
            <ProtectedRoute roles={[ROLE.ADMIN, ROLE.INGENIEUR]}>
              <RapportsPage />
            </ProtectedRoute>
          }
        />

        {/* ── Incidents & Commentaires — Admin + Ingénieur + Technicien ── */}
        <Route
          path="/moderation"
          element={
            <ProtectedRoute roles={[ROLE.ADMIN, ROLE.INGENIEUR, ROLE.TECHNICIEN]}>
              <IncidentsPage />
            </ProtectedRoute>
          }
        />
        {/* Alias pour les techniciens → même page */}
        <Route
          path="/technicien/anomalies"
          element={<Navigate to="/moderation" replace />}
        />

        {/* Administration — Administrateur uniquement */}
        <Route
          path="/administration"
          element={
            <ProtectedRoute roles={[ROLE.ADMIN]}>
              <AdministrationPage />
            </ProtectedRoute>
          }
        />
      </Routes>
    </Router>
  );
}

export default App;
