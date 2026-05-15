"""
routes/ia.py — Endpoints REST pour le moteur IA (Isolation Forest)
Expose les routes de prédiction, internes et de test de scénarios.
"""
from flask import Blueprint, request, jsonify

from auth.decorators import token_required
from ia.prediction import run_ai_prediction
from database.connection import connecter_base_de_donnees


ia_bp = Blueprint('ia_bp', __name__)


@ia_bp.route("/predict", methods=["GET"])
@token_required
def predict():
    """
    [AUTHENTIFIÉ] Déclenche manuellement le cycle de prédiction IA.
    Utilisé depuis le dashboard pour forcer une analyse immédiate.
    """
    return run_ai_prediction()


@ia_bp.route("/internal/predict", methods=["GET"])
def get_internal_ia_predictions():
    """
    [INTERNE] Endpoint sans authentification, accessible UNIQUEMENT
    depuis le conteneur 'simulation' via le réseau Docker interne.
    Déclenche l'Isolation Forest après chaque cycle de simulation.
    """
    return run_ai_prediction()


@ia_bp.route("/api/test-ia", methods=["POST"])
@token_required
def force_ia_incident():
    """
    [DÉMO] Injecte des métriques réseau extrêmes sur une antenne aléatoire
    pour déclencher une anomalie IA — utilisé pour les démonstrations live.
    Le statut final est exclusivement déterminé par l'Isolation Forest.
    """
    data          = request.get_json() or {}
    type_incident = data.get("type", "surchauffe")

    # Métriques de base (réseau sain)
    metrics = {
        "temp": 38.0, "cpu": 35.0, "signal": -62.0,
        "traffic": 120.0, "ram": 45.0, "latence": 18.0,
        "dispo": 99.5, "packet_loss": 0.2, "jitter": 4.0
    }

    # Scénarios d'anomalies selon le type demandé
    if type_incident == "surchauffe":
        metrics["temp"] = 91.0
        metrics["cpu"]  = 96.0
        metrics["ram"]  = 88.0
    elif type_incident == "surcharge":
        metrics["cpu"]         = 99.0
        metrics["traffic"]     = 950.0
        metrics["ram"]         = 97.0
        metrics["latence"]     = 280.0
        metrics["packet_loss"] = 8.0
    elif type_incident == "panne":
        metrics["dispo"]       = 55.0
        metrics["signal"]      = -118.0
        metrics["traffic"]     = 0.0
        metrics["packet_loss"] = 18.0
        metrics["latence"]     = 400.0

    try:
        conn = connecter_base_de_donnees()
        cur  = conn.cursor()
        cur.execute("SELECT id FROM antennes ORDER BY RANDOM() LIMIT 1")
        ant_id = cur.fetchone()[0]

        cur.execute("""
            INSERT INTO mesures
                (antenne_id, temperature, cpu, signal, traffic, ram,
                 latence, disponibilite, packet_loss, jitter, statut, date_mesure)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'analyse_ia_en_cours', NOW())
        """, (
            ant_id,
            metrics["temp"],  metrics["cpu"],     metrics["signal"],
            metrics["traffic"], metrics["ram"],   metrics["latence"],
            metrics["dispo"], metrics["packet_loss"], metrics["jitter"]
        ))
        conn.commit()
        cur.close(); conn.close()

        # Déclenche l'analyse IA immédiatement (appel interne via réseau Docker)
        import requests as _req
        _req.get("http://api:5000/internal/predict", timeout=15)

        return jsonify({
            "success": True,
            "antenne_id": ant_id,
            "message": f"Scénario '{type_incident}' injecté. Analyse IA en cours…"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
