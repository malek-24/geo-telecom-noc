/*
 * platformUrls.js  —  URLs des services de la plateforme SIG
 *
 * Ces URLs correspondent aux ports exposés dans docker-compose.yml :
 *   - GeoNetwork : port 8080
 *   - GeoServer  : port 8081
 *   - Grafana    : port 3001
 *
 * Ces liens sont affichés dans la barre de navigation (Topbar).
 */

export const platformUrls = {
  // Catalogue de métadonnées géographiques
  geonetwork: "http://localhost:8080/geonetwork/",

  // Serveur de cartes WMS/WFS
  geoserver: "http://localhost:8081/geoserver/web",

  // Tableau de bord de supervision Grafana
  grafana: "http://localhost:3001/",
};
