"""
routes/iot_routes.py — Endpoint de réception des données IoT (ESP32)
Métriques acceptées : temperature, cpu, signal, latence, disponibilite
Flux : ESP32 → POST /iot/mesure → insertion mesures → déclenchement IA
"""
import os
import requests
from datetime import datetime
from flask import Blueprint, request, jsonify

from database.connection import connecter_base_de_donnees

iot_bp = Blueprint('iot_bp', __name__)

IOT_API_KEY     = os.getenv("IOT_API_KEY", "esp32-noc-secret-2026")
API_PREDICT_URL = "http://localhost:5000/internal/predict"


def verifier_cle(req) -> bool:
    return req.headers.get("X-API-Key", "") == IOT_API_KEY


@iot_bp.route("/iot/mesure", methods=["POST"])
def recevoir_mesure_iot():
    """
    Reçoit une mesure JSON depuis un ESP32.

    Body JSON attendu :
    {
        "antenne_id":    1,
        "temperature":   42.5,
        "cpu":           35.0,    (optionnel)
        "signal":       -65.0,    (optionnel, RSSI WiFi réel de l'ESP32)
        "latence":       20.0,    (optionnel)
        "disponibilite": 99.5     (optionnel)
    }
    Header requis : X-API-Key: esp32-noc-secret-2026
    """
    if not verifier_cle(request):
        return jsonify({"error": "Clé API invalide ou manquante"}), 401

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Body JSON manquant"}), 400

    antenne_id  = data.get("antenne_id")
    temperature = data.get("temperature")

    if antenne_id is None or temperature is None:
        return jsonify({"error": "Champs requis : antenne_id, temperature"}), 400

    cpu          = float(data.get("cpu",          25.0))
    signal       = float(data.get("signal",      -65.0))
    latence      = float(data.get("latence",      15.0))
    disponibilite = float(data.get("disponibilite", 99.0))

    try:
        conn = connecter_base_de_donnees()
        cur  = conn.cursor()

        cur.execute("SELECT id, nom FROM antennes WHERE id = %s", (antenne_id,))
        antenne = cur.fetchone()
        if not antenne:
            cur.close(); conn.close()
            return jsonify({"error": f"Antenne ID {antenne_id} introuvable"}), 404

        cur.execute("""
            INSERT INTO mesures
                (antenne_id, temperature, cpu, signal, latence, disponibilite, statut, date_mesure)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            antenne_id,
            round(float(temperature), 1),
            round(cpu, 1),
            round(signal, 1),
            round(latence, 1),
            round(disponibilite, 1),
            "analyse_ia_en_cours",
            datetime.now()
        ))
        conn.commit()
        cur.close(); conn.close()

        print(f"[IoT] Antenne {antenne[1]} (ID={antenne_id}) — Temp={temperature}°C")

        # Déclenche l'analyse IA immédiatement
        try:
            requests.get(API_PREDICT_URL, timeout=30)
        except Exception:
            pass

        return jsonify({
            "success":     True,
            "message":     f"Mesure IoT reçue pour l'antenne {antenne[1]}",
            "antenne_id":  antenne_id,
            "temperature": temperature,
            "timestamp":   datetime.now().isoformat()
        }), 201

    except Exception as e:
        print(f"[IoT ERREUR] {e}")
        return jsonify({"error": str(e)}), 500


@iot_bp.route("/iot/status", methods=["GET"])
def iot_status():
    """Vérifie que la passerelle IoT est active."""
    return jsonify({
        "status":    "online",
        "service":   "GEO-TÉLÉCOM NOC IoT Gateway",
        "version":   "2.0",
        "metriques": ["temperature", "cpu", "signal", "latence", "disponibilite"],
        "timestamp": datetime.now().isoformat()
    })


@iot_bp.route("/iot/antenne/<int:ant_id>/dernieres", methods=["GET"])
def dernieres_mesures_iot(ant_id):
    """Retourne les 10 dernières mesures d'une antenne (debug ESP32)."""
    if not verifier_cle(request):
        return jsonify({"error": "Clé API invalide"}), 401
    try:
        conn = connecter_base_de_donnees()
        cur  = conn.cursor()
        cur.execute("""
            SELECT temperature, cpu, signal, latence, disponibilite,
                   statut, to_char(date_mesure, 'YYYY-MM-DD HH24:MI:SS') AS date_mesure
            FROM mesures
            WHERE antenne_id = %s
            ORDER BY date_mesure DESC
            LIMIT 10
        """, (ant_id,))
        cols = [d[0] for d in cur.description]
        rows = [dict(zip(cols, row)) for row in cur.fetchall()]
        cur.close(); conn.close()
        return jsonify({"antenne_id": ant_id, "mesures": rows})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
