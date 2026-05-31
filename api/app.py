"""
app.py — Point d'entrée de l'API Flask (GEO-TÉLÉCOM NOC Platform)
Enregistre tous les blueprints et configure les middlewares globaux.
"""
import os
from flask import Flask, jsonify
from flask_cors import CORS

from routes.auth_routes      import auth_bp
from routes.antennes_routes  import network_bp
from routes.ia               import ia_bp
from routes.incidents_routes import incidents_bp
from routes.reports_routes   import reports_bp
from routes.dashboard_routes import admin_bp
from routes.iot_routes       import iot_bp
from routes.chat_routes      import chat_bp   # ← Chat privé
from routes.audit_routes     import audit_bp
from routes.export_routes    import export_bp

app = Flask(__name__)
CORS(app, supports_credentials=True)

# Au démarrage : 121 antennes Normal, 0 incident (nettoyage démo)
def _bootstrap_au_demarrage():
    import time
    for tentative in range(1, 16):
        try:
            from database.connection import connecter_base_de_donnees
            from ia.prediction import bootstrap_reseau_normal

            conn = connecter_base_de_donnees()
            from utils.db_extensions import initialiser_tables_extensions
            initialiser_tables_extensions(conn)
            cur  = conn.cursor()
            cur.close()
            if os.getenv("NOC_STARTUP_RESET", "1") == "1":
                bootstrap_reseau_normal(conn)
            conn.close()
            return
        except Exception as e:
            print(f"[BOOTSTRAP] Tentative {tentative}/15 — {e}")
            time.sleep(2)


_bootstrap_au_demarrage()

# ── Blueprints ────────────────────────────────────────────────────
app.register_blueprint(auth_bp)
app.register_blueprint(network_bp)
app.register_blueprint(ia_bp)
app.register_blueprint(incidents_bp)
app.register_blueprint(reports_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(iot_bp)
app.register_blueprint(chat_bp)              # ← Chat privé
app.register_blueprint(audit_bp)
app.register_blueprint(export_bp)

# ── Healthcheck (pour Docker) ─────────────────────────────────────
@app.route("/", methods=["GET"])
def index():
    """Page d'accueil API — évite le 404 sur http://localhost:7000"""
    return jsonify({
        "status":  "ok",
        "service": "GEO-TÉLÉCOM NOC API",
        "version": "PFE 2025/2026",
        "endpoints": {
            "health":        "/health",
            "login":         "POST /auth/login",
            "dashboard":     "/dashboard/summary",
            "antennes":      "/antennes",
            "iot_mesure":    "POST /iot/mesure",
            "iot_status":    "/iot/status",
            "predict":       "GET /predict  (Bearer JWT)",
        },
        "frontend": "http://localhost:3000",
    }), 200


@app.route("/health", methods=["GET"])
def health():
    """Vérifie que le serveur Flask est opérationnel."""
    return jsonify({"status": "ok", "service": "GEO-TÉLÉCOM NOC API"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
