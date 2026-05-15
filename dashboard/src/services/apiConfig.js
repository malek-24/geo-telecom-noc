import axios from 'axios';

export const API_BASE_URL = "/api";

// Création d'une instance Axios globale
const api = axios.create({
  baseURL: API_BASE_URL,
});

// Intercepteur pour ajouter le token JWT à chaque requête
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('geo_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
}, (error) => {
  return Promise.reject(error);
});

// Intercepteur pour gérer les erreurs globales (ex: Token expiré)
api.interceptors.response.use((response) => {
  return response;
}, (error) => {
  if (error.response && error.response.status === 401) {
    // Si 401 Unauthorized, on efface le token et on redirige
    console.error("Session expirée ou non autorisée. Redirection vers login.");
    localStorage.removeItem('geo_token');
    localStorage.removeItem('geo_username');
    localStorage.removeItem('geo_role');
    // On redirige brutalement vers la page de login pour sécuriser
    if (window.location.pathname !== '/login') {
      window.location.href = '/login?expired=true';
    }
  }
  return Promise.reject(error);
});

export default api;
