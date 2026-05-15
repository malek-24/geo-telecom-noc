/*
 * setupProxy.js  —  Proxy de développement local (npm start)
 *
 * Ce fichier est utilisé UNIQUEMENT pendant le développement local (npm start).
 * Il redirige les appels /api vers l'API Flask sur localhost:5000.
 *
 * En production (Docker), nginx gère ce proxy via nginx.conf.
 *
 * Note : notre apiConfig.js pointe directement vers http://localhost:5000
 * donc ce fichier sert de fallback si on utilise un préfixe /api.
 */

const { createProxyMiddleware } = require("http-proxy-middleware");

module.exports = function (app) {
  app.use(
    "/api",
    createProxyMiddleware({
      target: "http://localhost:5000",  // Adresse de l'API Flask locale
      changeOrigin: true,
      pathRewrite: { "^/api": "" },     // /api/stats → /stats
    })
  );
};
