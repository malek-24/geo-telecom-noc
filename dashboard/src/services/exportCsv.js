import axios from 'axios';
import { API_BASE_URL, authCfg } from './apiConfig';

/** Télécharge un export CSV depuis l'API Flask. */
export async function downloadCsv(token, endpoint, filename) {
  const res = await axios.get(`${API_BASE_URL}${endpoint}`, {
    ...authCfg(token),
    responseType: 'blob',
  });
  const url = window.URL.createObjectURL(new Blob([res.data]));
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', filename);
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
}
