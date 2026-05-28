import axios from 'axios';

/** Préfixe API (proxy CRA → Flask en dev, nginx en prod). */
export const API_BASE_URL = '/api';

/** En-têtes JWT pour les requêtes authentifiées. */
export function authCfg(token) {
  return { headers: { Authorization: `Bearer ${token}` } };
}

export default axios;
