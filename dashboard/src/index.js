/*
 * index.js  —  Point d'entrée de l'application React
 *
 * Ce fichier est le tout premier fichier exécuté par React.
 * Il monte l'application dans le div#root du fichier public/index.html.
 *
 * Structure :
 *   AuthProvider → fournit la session à toute l'application
 *     App        → contient le routing et toutes les pages
 */

import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import { AuthProvider } from "./auth/AuthContext";

// Styles CSS de la bibliothèque de cartes Leaflet (obligatoire pour l'affichage)
import "leaflet/dist/leaflet.css";

// Styles CSS personnalisés de l'application
import "./styles.css";

// Trouver l'élément HTML <div id="root"> dans public/index.html
const racine = ReactDOM.createRoot(document.getElementById("root"));

// Monter l'application React
racine.render(
  // AuthProvider enveloppe toute l'application pour partager la session
  <AuthProvider>
    <App />
  </AuthProvider>
);
