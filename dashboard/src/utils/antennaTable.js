/**
 * Tri et filtrage du tableau Antennes (page /equipments).
 * Utilisé uniquement côté interface — les données viennent de GET /antennes.
 */

const ORDRE_STATUT = { critique: 0, alerte: 1, maintenance: 2, normal: 3, en_attente: 4 };

/** Colonnes affichées dans le tableau (clé = champ API) */
export const TABLE_COLUMNS = [
  { key: 'nom', label: 'Site' },
  { key: 'zone', label: 'Zone' },
  { key: 'type', label: 'Type' },
  { key: 'cpu', label: 'CPU (%)', numeric: true },
  { key: 'temperature', label: 'Temp (°C)', numeric: true },
  { key: 'disponibilite', label: 'Dispo (%)', numeric: true },
  { key: 'latence', label: 'Latence (ms)', numeric: true },
  { key: 'risk_score', label: 'Score IA', numeric: true },
  { key: 'statut', label: 'Statut' },
  { key: 'latitude', label: 'Coordonnées', numeric: true },
];

function valeurTri(ligne, cle) {
  if (cle === 'statut') return ORDRE_STATUT[ligne.statut] ?? 9;
  const v = ligne[cle];
  if (v === undefined || v === null || v === '') return null;
  const col = TABLE_COLUMNS.find(c => c.key === cle);
  if (col?.numeric) {
    const n = Number(v);
    return Number.isFinite(n) ? n : null;
  }
  return String(v).toLowerCase();
}

export function sortAntennas(lignes, cle, direction) {
  return [...lignes].sort((a, b) => {
    const va = valeurTri(a, cle);
    const vb = valeurTri(b, cle);
    if (va === null && vb === null) return 0;
    if (va === null) return 1;
    if (vb === null) return -1;
    if (va < vb) return direction === 'asc' ? -1 : 1;
    if (va > vb) return direction === 'asc' ? 1 : -1;
    return 0;
  });
}

export function filterAntennas(lignes, { search, filterZone, filterStatut }) {
  const q = (search || '').trim().toLowerCase();
  return lignes.filter(a => {
    if (filterZone && a.zone !== filterZone) return false;
    if (filterStatut && a.statut !== filterStatut) return false;
    if (!q) return true;
    return (
      a.nom?.toLowerCase().includes(q) ||
      a.zone?.toLowerCase().includes(q)
    );
  });
}
