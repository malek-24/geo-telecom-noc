/*
 * Alerts.js  —  Composant liste des alertes
 *
 * Affiche la liste des antennes en alerte ou critique.
 *
 * Props :
 *   - alerts  : tableau des alertes reçu depuis l'API
 *   - loading : true si les données sont encore en cours de chargement
 */

export default function Alerts({ alerts, loading }) {

  // ── Pendant le chargement ──
  if (loading) {
    return (
      <div className="alerts">
        <h3>Alertes récentes</h3>
        <p>Chargement…</p>
      </div>
    );
  }

  // ── Aucune alerte active ──
  if (!alerts || alerts.length === 0) {
    return (
      <div className="alerts">
        <h3>Alertes récentes</h3>
        <p>✅ Aucune alerte active</p>
      </div>
    );
  }

  // ── Afficher la liste des alertes ──
  return (
    <div className="alerts">
      <h3>Alertes récentes ({alerts.length})</h3>

      {alerts.map((alerte, index) => (
        <div key={index} className={`alert-item alert-${alerte.statut}`}>
          {/* Emoji selon le niveau d'alerte */}
          {alerte.statut === "critique" ? "🔴" : "🟠"}{" "}

          {/* Informations de l'antenne */}
          <strong>{alerte.nom}</strong> | Zone : {alerte.zone} |{" "}
          Temp : {alerte.temperature}°C | CPU : {alerte.cpu}% |{" "}
          <span className={`badge badge-${alerte.statut}`}>
            {alerte.statut.toUpperCase()}
          </span>
        </div>
      ))}
    </div>
  );
}