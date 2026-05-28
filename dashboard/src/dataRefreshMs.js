/**
 * Intervalles de rafraîchissement automatique (polling silencieux, sans rechargement de page).
 */
export const REFRESH_MS = {
  dashboard: 15000,
  map: 15000,
  antennes: 15000,
  incidents: 10000,
  admin: 30000,
  chat: 5000,
  criticalBanner: 15000,
};

/** @deprecated Utiliser REFRESH_MS — conservé pour imports existants */
export const DATA_REFRESH_MS = REFRESH_MS.dashboard;
