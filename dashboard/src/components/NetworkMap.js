/*
 * NetworkMap.js  —  Carte interactive des antennes réseau
 *
 * Ce composant affiche une carte Leaflet (OpenStreetMap) avec :
 *   - Les antennes représentées par des cercles colorés selon leur statut
 *       🟢 vert  = normal
 *       🟡 jaune = alerte
 *       🔴 rouge = critique
 *   - Les liaisons fibre optique calculées par l'algorithme MST (Arbre couvrant minimal)
 *   - Un panneau d'alertes à droite (si showAlertsPanel = true)
 *
 * Props :
 *   - height         : hauteur de la carte (ex: "500px")
 *   - showAlertsPanel: afficher ou non le panneau des alertes (défaut: true)
 */

import React, { useEffect, useState } from "react";
import { MapContainer, TileLayer, Circle, CircleMarker, Polyline, Tooltip, useMap } from "react-leaflet";
import { API_BASE_URL } from "../services/apiConfig";
import { DATA_REFRESH_MS } from "../dataRefreshMs";
import { platformUrls } from "../platformUrls";

// =============================================================
// ALGORITHME : Distance Haversine
// Calcule la distance en kilomètres entre deux points GPS.
// Formule mathématique standard pour les distances sur une sphère.
// =============================================================
function calculerDistanceKm(pointA, pointB) {
  const RAYON_TERRE_KM = 6371;

  // Convertir les degrés en radians
  const deltaLat = ((pointB[0] - pointA[0]) * Math.PI) / 180;
  const deltaLon = ((pointB[1] - pointA[1]) * Math.PI) / 180;

  const a =
    Math.sin(deltaLat / 2) * Math.sin(deltaLat / 2) +
    Math.cos((pointA[0] * Math.PI) / 180) *
    Math.cos((pointB[0] * Math.PI) / 180) *
    Math.sin(deltaLon / 2) * Math.sin(deltaLon / 2);

  return RAYON_TERRE_KM * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

// =============================================================
// ALGORITHME : Arbre Couvrant Minimal (MST — Prim's algorithm)
// Connecte toutes les antennes avec le minimum de câble fibre.
// Résultat : liste de segments [pointA, pointB] à dessiner sur la carte.
// =============================================================
function construireReseauFibre(antennes) {
  if (antennes.length < 2) return [];

  // Convertir les antennes en tableau de coordonnées [lat, lon]
  const points = antennes.map((a) => [a.latitude, a.longitude]);

  // Ensemble des points déjà dans l'arbre (on commence par le premier)
  const dansLArbre = new Set([0]);
  const segments = [];

  // Tant que tous les points ne sont pas connectés
  while (dansLArbre.size < points.length) {
    let meilleureDistance = Infinity;
    let meilleurDepart   = -1;
    let meilleurArrivee  = -1;

    // Trouver le point le plus proche non encore connecté
    for (const i of dansLArbre) {
      for (let j = 0; j < points.length; j++) {
        if (dansLArbre.has(j)) continue; // Déjà dans l'arbre
        const distance = calculerDistanceKm(points[i], points[j]);
        if (distance < meilleureDistance) {
          meilleureDistance = distance;
          meilleurDepart    = i;
          meilleurArrivee   = j;
        }
      }
    }

    if (meilleurArrivee === -1) break;

    // Ajouter ce segment à l'arbre
    segments.push([points[meilleurDepart], points[meilleurArrivee]]);
    dansLArbre.add(meilleurArrivee);
  }

  return segments;
}

// Calculer la longueur totale du réseau fibre (somme des segments)
function calculerLongueurTotaleKm(segments) {
  const total = segments.reduce(
    (somme, seg) => somme + calculerDistanceKm(seg[0], seg[1]),
    0
  );
  return Math.round(total);
}

// =============================================================
// Sous-composant : Ajuster le zoom de la carte sur les antennes
// useMap() accède à l'instance Leaflet depuis un composant enfant.
// =============================================================
function AjusterVue({ antennes }) {
  const carte = useMap();
  const [zoomFait, setZoomFait] = useState(false);

  useEffect(() => {
    if (antennes.length > 0 && !zoomFait) {
      const coordonnees = antennes.map((a) => [a.latitude, a.longitude]);
      carte.fitBounds(coordonnees, { padding: [30, 30] });
      setZoomFait(true);
    }
  }, [antennes, carte, zoomFait]);

  return null; // Ce composant ne rend rien visuellement
}

// =============================================================
// COMPOSANT PRINCIPAL : NetworkMap
// =============================================================
export default function NetworkMap({ height = "500px", showAlertsPanel = true }) {

  // État : liste des antennes chargées depuis l'API
  const [antennes, setAntennes]       = useState([]);
  // État : segments du réseau fibre (résultat MST)
  const [segmentsFibre, setSegmentsFibre] = useState([]);
  // État : longueur totale du réseau en km
  const [longueurKm, setLongueurKm]   = useState(0);
  // État : alertes chargées depuis l'API
  const [alertes, setAlertes]         = useState([]);
  // État : heure de la dernière mise à jour
  const [derniereMaj, setDerniereMaj] = useState(null);
  // État : chargement en cours
  const [chargement, setChargement]   = useState(true);

  // ── Chargement des antennes ──
  function chargerAntennes(initial = false) {
    if (initial) setChargement(true);

    // Charger les antennes ET les prédictions IA en parallèle
    Promise.all([
      fetch(`${API_BASE_URL}/antennes`).then(res => res.ok ? res.json() : []),
      fetch(`${API_BASE_URL}/predict`).then(res => res.ok ? res.json() : []).catch(() => [])
    ])
      .then(([dataAntennes, dataIA]) => {
        // Fusionner les données pour marquer les anomalies
        const merged = dataAntennes.map(ant => {
          const pred = dataIA.find(p => p.id === ant.id);
          return { ...ant, isAnomaly: pred?.anomaly === 1 };
        });

        // Construire le réseau fibre à partir des nouvelles antennes
        const segments = construireReseauFibre(merged);

        setAntennes(merged);
        setSegmentsFibre(segments);
        setLongueurKm(calculerLongueurTotaleKm(segments));
        setDerniereMaj(new Date().toLocaleTimeString("fr-FR"));

        if (initial) setChargement(false);
      })
      .catch(() => {
        if (initial) setChargement(false);
      });
  }

  // ── Chargement des alertes (seulement si le panneau est visible) ──
  function chargerAlertes() {
    if (!showAlertsPanel) return;

    fetch(`${API_BASE_URL}/alerts`)
      .then((res) => (res.ok ? res.json() : []))
      .then((donnees) => {
        setAlertes(Array.isArray(donnees) ? donnees : []);
      })
      .catch(() => {});
  }

  // ── Démarrer les chargements + rafraîchissement automatique ──
  useEffect(() => {
    chargerAntennes(true);
    chargerAlertes();

    // Répéter toutes les DATA_REFRESH_MS millisecondes
    const minuterie = setInterval(() => {
      chargerAntennes(false);
      chargerAlertes();
    }, DATA_REFRESH_MS);

    return () => clearInterval(minuterie); // Nettoyage
  }, []);

  // ── Couleur du marqueur selon le statut ──
  function couleurStatut(statut) {
    if (statut === "critique") return "#ef4444"; // Rouge
    if (statut === "alerte")   return "#f59e0b"; // Orange
    return "#22c55e";                            // Vert
  }

  // ── SITES PROJETÉS (Simulation Figma) ──
  const SITES_PROJETES = [
    { id: 'p1', nom: "Site 5G Hiboun (Projet)", lat: 35.520, lon: 11.050 },
    { id: 'p2', nom: "Site 5G Mahdia Port (Projet)", lat: 35.504, lon: 11.070 },
    { id: 'p3', nom: "Site 5G Rejiche Sud (Projet)", lat: 35.450, lon: 11.020 },
  ];

  // Centre par défaut (Mahdia)
  const centreDefaut = [35.35, 11.0];

  // Calcul des compteurs pour la légende
  const nbNormal   = antennes.filter(a => a.statut === 'normal').length;
  const nbAlerte   = antennes.filter(a => a.statut === 'alerte').length;
  const nbCritique = antennes.filter(a => a.statut === 'critique').length;

  return (
    <div className="map-section">
      <div className="map-wrapper" style={{ height }}>

        {/* ── Affichage pendant le chargement ── */}
        {chargement ? (
          <div className="map-loading">
            <div className="map-loading-spinner" />
            <span>Chargement des antennes en temps réel...</span>
          </div>
        ) : (
          /* ── Carte Leaflet ── */
          <MapContainer
            center={centreDefaut}
            zoom={10}
            style={{ height: "100%", width: "100%" }}
          >
            {/* Fond de carte OpenStreetMap (style Carto) */}
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a> &copy; <a href="https://carto.com/">CARTO</a>'
              url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
            />

            {/* Liaisons fibre (traits bleus) */}
            {segmentsFibre.map((segment, index) => (
              <Polyline
                key={`fibre-${index}`}
                positions={segment}
                pathOptions={{ color: "#3b82f6", weight: 2, opacity: 0.7 }}
              />
            ))}

            {/* Marqueurs des antennes (cercles colorés) */}
            {antennes.map((antenne) => (
              <React.Fragment key={`group-${antenne.id}`}>
                {/* Zone de couverture (Cercle en mètres) */}
                <Circle
                  center={[antenne.latitude, antenne.longitude]}
                  radius={800} // Rayon de couverture : 800 mètres
                  pathOptions={{
                    color:       couleurStatut(antenne.statut),
                    fillColor:   couleurStatut(antenne.statut),
                    fillOpacity: 0.15, // Très transparent pour ne pas surcharger
                    weight:      1,
                    dashArray:   "5, 5" // Bordure en pointillés pour un look "zone"
                  }}
                />

                <CircleMarker
                  center={[antenne.latitude, antenne.longitude]}
                  radius={antenne.statut === "critique" ? 10 : 8}
                  pathOptions={{
                    color:       antenne.isAnomaly ? "#a855f7" : couleurStatut(antenne.statut), // Violet si anomalie IA
                    fillColor:   couleurStatut(antenne.statut),
                    fillOpacity: 0.9,
                    weight:      antenne.isAnomaly ? 4 : 2, // Bordure plus épaisse si anomalie
                  }}
                >
                  <Tooltip>
                    <div>
                      <strong>{antenne.nom}</strong> {antenne.isAnomaly && " (⚠️ ANOMALIE IA)"}<br />
                      Zone : {antenne.zone}<br />
                      Statut : <strong style={{ color: couleurStatut(antenne.statut) }}>
                        {antenne.statut?.toUpperCase()}
                      </strong><br />
                      Temp : {antenne.temperature}°C &nbsp;|&nbsp; CPU : {antenne.cpu}%
                    </div>
                  </Tooltip>
                </CircleMarker>
              </React.Fragment>
            ))}

            {/* SITES PROJETÉS (Étoiles violettes) */}
            {SITES_PROJETES.map((site) => (
              <CircleMarker
                key={site.id}
                center={[site.lat, site.lon]}
                radius={10}
                pathOptions={{
                  color: "#a855f7", // Violet
                  fillColor: "#a855f7",
                  fillOpacity: 0.8,
                  weight: 2
                }}
              >
                <Tooltip permanent direction="top" className="tooltip-projected">
                  <span>⭐ {site.nom}</span>
                </Tooltip>
              </CircleMarker>
            ))}

            {/* Ajuster le zoom pour voir toutes les antennes */}
            {antennes.length > 0 && <AjusterVue antennes={antennes} />}
          </MapContainer>
        )}

        {/* ── Légende de la carte ── */}
        {!chargement && (
          <div className="map-legend">
            <div className="legend-item">
              <span className="legend-dot" style={{ background: "#22c55e" }} />
              Opérationnelles ({nbNormal})
            </div>
            <div className="legend-item">
              <span className="legend-dot" style={{ background: "#f59e0b" }} />
              Alertes ({nbAlerte})
            </div>
            <div className="legend-item">
              <span className="legend-dot" style={{ background: "#ef4444" }} />
              Pannes ({nbCritique})
            </div>
            <div className="legend-item">
              <span className="legend-line" style={{ background: "#3b82f6" }} />
              Réseau Fibre
            </div>
            <div className="legend-item">
              <span className="legend-dot" style={{ background: "#a855f7" }} />
              Sites Projetés (⭐)
            </div>
            {derniereMaj && (
              <div className="legend-update">🔄 {derniereMaj}</div>
            )}
          </div>
        )}
      </div>

      {/* ── Panneau des alertes (à droite de la carte) ── */}
      {showAlertsPanel && (
        <div className="ai-panel map-alerts-panel">
          <div className="ai-panel-header">
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <span>⚠️</span>
              <strong>Alertes</strong>
              {alertes.length > 0 && (
                <span className="map-alerts-count">({alertes.length})</span>
              )}
            </div>
            {/* Liens rapides vers les services SIG */}
            <div className="ai-panel-external">
              <a href={platformUrls.geonetwork} target="_blank" rel="noreferrer" className="geonetwork-link">
                GeoNetwork
              </a>
              <a href={platformUrls.geoserver} target="_blank" rel="noreferrer" className="geonetwork-link">
                GeoServer
              </a>
            </div>
          </div>

          <div className="map-alerts-body">
            {alertes.length === 0 ? (
              <p className="text-muted map-alerts-empty">Aucune alerte active.</p>
            ) : (
              <div className="map-alerts-table-scroll">
                <table className="data-table map-alerts-table">
                  <thead>
                    <tr>
                      <th>Antenne</th>
                      <th>Zone</th>
                      <th>Statut</th>
                      <th>Temp.</th>
                      <th>CPU</th>
                    </tr>
                  </thead>
                  <tbody>
                    {alertes.map((a) => (
                      <tr key={`${a.id}-${a.date_mesure}`} className="alert-row">
                        <td><strong>{a.nom}</strong></td>
                        <td>{a.zone}</td>
                        <td>
                          <span className={`badge badge-${a.statut}`}>
                            {String(a.statut || "").toUpperCase()}
                          </span>
                        </td>
                        <td>{a.temperature != null ? `${Number(a.temperature).toFixed(1)}°` : "—"}</td>
                        <td>{a.cpu != null ? `${Number(a.cpu).toFixed(0)}%` : "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
