"""
routes/iot_routes.py — Endpoint de réception des données IoT (ESP32)
=====================================================================
Permet à un ESP32 équipé d'un capteur de température (DHT22 / DS18B20)
d'envoyer ses mesures directement dans la base de données PostgreSQL,
en les associant à une antenne réelle via son antenne_id.

Endpoint public (pas de JWT requis) — sécurisé par clé API secrète.

Flux :
  ESP32 → POST /iot/mesure → insertion mesures → déclenchement IA
"""

from datetime import datetime
from flask import Blueprint, request, jsonify
import psycopg2
import os
import requests

from database.connection import connecter_base_de_donnees

iot_bp = Blueprint('iot_bp', __name__)

# ─── Clé API secrète partagée avec l'ESP32 ──────────────────────────────────
IOT_API_KEY = os.getenv("IOT_API_KEY", "esp32-noc-secret-2026")
API_PREDICT_URL = "http://localhost:5000/internal/predict"


def verifier_cle(req) -> bool:
    """Vérifie la clé API dans le header X-API-Key."""
    return req.headers.get("X-API-Key", "") == IOT_API_KEY


# ─── Réception d'une mesure IoT ─────────────────────────────────────────────
@iot_bp.route("/iot/mesure", methods=["POST"])
def recevoir_mesure_iot():
    """
    Reçoit une mesure JSON depuis un ESP32 et l'insère dans la table mesures.

    Body JSON attendu :
    {
        "antenne_id":  1,          // ID de l'antenne à laquelle l'ESP32 est rattaché
        "temperature": 42.5,       // Température lue par DHT22/DS18B20 (°C)
        "cpu":         35.0,       // Optionnel — simulé si absent
        "ram":         40.0,       // Optionnel
        "signal":      -65.0,      // Optionnel
        "traffic":     150.0,      // Optionnel
        "latence":     20.0,       // Optionnel
        "disponibilite": 99.5,     // Optionnel
        "packet_loss": 0.1,        // Optionnel
        "jitter":      3.0         // Optionnel
    }

    Header requis :
        X-API-Key: esp32-noc-secret-2026
    """
    # ── Vérification clé API ────────────────────────────────────────────────
    if not verifier_cle(request):
        return jsonify({"error": "Clé API invalide ou manquante"}), 401

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Body JSON manquant"}), 400

    antenne_id = data.get("antenne_id")
    temperature = data.get("temperature")

    if antenne_id is None or temperature is None:
        return jsonify({"error": "Champs requis : antenne_id, temperature"}), 400

    # ── Valeurs optionnelles avec defaults raisonnables ─────────────────────
    cpu          = float(data.get("cpu",          25.0))
    ram          = float(data.get("ram",          30.0))
    signal       = float(data.get("signal",      -65.0))
    traffic      = float(data.get("traffic",     100.0))
    latence      = float(data.get("latence",      15.0))
    disponibilite= float(data.get("disponibilite", 99.0))
    packet_loss  = float(data.get("packet_loss",   0.1))
    jitter       = float(data.get("jitter",        2.0))

    try:
        conn = connecter_base_de_donnees()
        cur  = conn.cursor()

        # ── Vérifier que l'antenne existe ───────────────────────────────────
        cur.execute("SELECT id, nom FROM antennes WHERE id = %s", (antenne_id,))
        antenne = cur.fetchone()
        if not antenne:
            cur.close(); conn.close()
            return jsonify({"error": f"Antenne ID {antenne_id} introuvable"}), 404

        # ── Insertion de la mesure IoT ──────────────────────────────────────
        cur.execute("""
            INSERT INTO mesures
                (antenne_id, temperature, cpu, ram, signal, traffic,
                 latence, disponibilite, packet_loss, jitter,
                 statut, date_mesure)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            antenne_id,
            round(float(temperature), 1),
            round(cpu, 1), round(ram, 1),
            round(signal, 1), round(traffic, 1),
            round(latence, 1), round(disponibilite, 1),
            round(packet_loss, 2), round(jitter, 1),
            "analyse_ia_en_cours",
            datetime.now()
        ))
        conn.commit()
        cur.close(); conn.close()

        print(f"[IoT] Mesure reçue — Antenne {antenne[1]} (ID={antenne_id}) — Temp={temperature}°C")

        # ── Déclenche l'analyse IA immédiatement ───────────────────────────
        try:
            requests.get(API_PREDICT_URL, timeout=30)
        except Exception:
            pass  # L'IA sera déclenchée au prochain cycle simulation

        return jsonify({
            "success":    True,
            "message":    f"Mesure IoT reçue pour l'antenne {antenne[1]}",
            "antenne_id": antenne_id,
            "temperature": temperature,
            "timestamp":  datetime.now().isoformat()
        }), 201

    except Exception as e:
        print(f"[IoT ERREUR] {e}")
        return jsonify({"error": str(e)}), 500


# ─── Status de l'endpoint IoT ───────────────────────────────────────────────
@iot_bp.route("/iot/status", methods=["GET"])
def iot_status():
    """Endpoint de test — vérifie que la passerelle IoT est active."""
    return jsonify({
        "status":   "online",
        "service":  "GEO-TÉLÉCOM NOC IoT Gateway",
        "version":  "1.0",
        "endpoint": "POST /iot/mesure",
        "timestamp": datetime.now().isoformat()
    })


# ─── Liste des dernières mesures IoT d'une antenne ──────────────────────────
@iot_bp.route("/iot/antenne/<int:ant_id>/dernieres", methods=["GET"])
def dernieres_mesures_iot(ant_id):
    """
    Retourne les 10 dernières mesures d'une antenne (utile pour debug ESP32).
    Header requis : X-API-Key
    """
    if not verifier_cle(request):
        return jsonify({"error": "Clé API invalide"}), 401

    try:
        conn = connecter_base_de_donnees()
        cur  = conn.cursor()
        cur.execute("""
            SELECT temperature, cpu, ram, signal, latence,
                   packet_loss, disponibilite, statut,
                   to_char(date_mesure, 'YYYY-MM-DD HH24:MI:SS') AS date_mesure
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
