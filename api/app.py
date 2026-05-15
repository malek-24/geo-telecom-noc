"""
app.py — Point d'entrée de l'API Flask (GEO-TÉLÉCOM NOC Platform)
Enregistre tous les blueprints et configure les middlewares globaux.
"""
import os
from flask import Flask, jsonify
from flask_cors import CORS

from routes.auth_routes   import auth_bp
from routes.antennes_routes import network_bp
from routes.ia            import ia_bp
from routes.incidents_routes import incidents_bp
from routes.reports_routes   import reports_bp
from routes.dashboard_routes import admin_bp

app = Flask(__name__)
CORS(app, supports_credentials=True)

# ── Blueprints ────────────────────────────────────────────────────
app.register_blueprint(auth_bp)
app.register_blueprint(network_bp)
app.register_blueprint(ia_bp)
app.register_blueprint(incidents_bp)
app.register_blueprint(reports_bp)
app.register_blueprint(admin_bp)

# ── Healthcheck (pour Docker) ─────────────────────────────────────
@app.route("/health", methods=["GET"])
def health():
    """Vérifie que le serveur Flask est opérationnel."""
    return jsonify({"status": "ok", "service": "GEO-TÉLÉCOM NOC API"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
