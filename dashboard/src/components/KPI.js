/*
 * KPI.js  —  Composant "Indicateur Clé de Performance"
 *
 * Affiche un grand chiffre avec un titre, utilisé dans le dashboard
 * pour montrer les statistiques principales (nombre d'antennes, etc.)
 *
 * Props (paramètres) :
 *   - title : le titre de l'indicateur (ex: "Antennes actives")
 *   - value : la valeur à afficher (ex: 42)
 *   - color : la couleur de la valeur
 */

export default function KPI({ title, value, color }) {
  return (
    <div className="kpi">
      {/* Titre de l'indicateur (en petit) */}
      <h3>{title}</h3>

      {/* Valeur principale (en grand) */}
      <h1 style={{ color: color || "inherit" }}>
        {value ?? 0}
      </h1>
    </div>
  );
}