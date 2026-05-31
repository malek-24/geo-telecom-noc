"""
routes/iot_routes.py — Endpoint de réception des données IoT
============================================================
GEO-TELECOM NOC — Antenne ISET Mahdia (Arduino Uno + DHT11)
PFE Licence — Réseaux & Télécommunications 2025/2026

FLUX COMPLET :
  Arduino Uno + DHT11
      ↓ (JSON Serial USB)
  serial_bridge.py
      ↓ (POST /iot/mesure)
  Cet endpoint
      ↓
  Base de données (temperature réelle + CPU/signal/latence/dispo simulés MRRW)
      ↓
  Isolation Forest (analyse ciblée ISET Mahdia uniquement)
      ↓
  Score santé → État → Alerte
      ↓
  Dashboard

FORMAT JSON ATTENDU (depuis Arduino via serial_bridge.py) :
  {"antenne_id": 121, "temperature": 28.5}

  La température vient du capteur DHT11 (réelle).
  Les autres métriques (cpu, signal, latence, dispo) sont simulées
  avec le même algorithme MRRW que les autres antennes.

RÈGLE IMPORTANTE :
  L'antenne ISET Mahdia est traitée exactement comme toutes les autres.
  Même pipeline IA, même calcul de score, même détermination du statut.
  Aucune règle spéciale.
"""
import os
import random
from datetime import datetime
from flask import Blueprint, request, jsonify

from database.connection import connecter_base_de_donnees

iot_bp = Blueprint('iot_bp', __name__)

IOT_API_KEY = os.getenv("IOT_API_KEY", "esp32-noc-secret-2026")

# ── Paramètres MRRW pour ISET Mahdia ──────────────────────────────
# Même algorithme que le simulateur principal (generate_mesures.py)
# Valeurs légèrement adaptées à la zone Mahdia Nord (côtière)
ALPHA = 0.15   # Vitesse de retour vers la cible

# Profil ISET Mahdia — mêmes cibles MRRW que le simulateur réseau
PROFIL_ISET = {
    "cpu":     {"cible": 40.0,  "bmin": 36.0,   "bmax": 44.0,   "bruit": 0.3},
    "signal":  {"cible": -65.0, "bmin": -71.0,  "bmax": -59.0,  "bruit": 0.15},
    "latence": {"cible": 15.0,  "bmin": 13.5,   "bmax": 16.5,   "bruit": 0.1},
    "dispo":   {"cible": 99.0,  "bmin": 97.0,   "bmax": 100.0,  "bruit": 0.01},
}


def verifier_cle(req) -> bool:
    """Vérifie la clé API dans le header X-API-Key."""
    return req.headers.get("X-API-Key", "") == IOT_API_KEY


def _mrrw(prev: float, profil: dict) -> float:
    """
    Applique le Mean-Reverting Random Walk pour une métrique simulée.

    Formule : val = prev + alpha × (cible - prev) + bruit
      - alpha = 0.15 : retour progressif vers la cible
      - bruit gaussien léger pour un aspect naturel

    Paramètres :
      prev   : valeur précédente de la métrique
      profil : dict avec {"cible", "bmin", "bmax", "bruit"}

    Retour :
      Nouvelle valeur, clippée dans les bornes physiques.
    """
    val = prev + ALPHA * (profil["cible"] - prev) + random.gauss(0, profil["bruit"])
    return round(max(profil["bmin"], min(profil["bmax"], val)), 2)


def _lire_mesure_precedente(conn, antenne_id: int) -> dict:
    """
    Lit la dernière mesure connue de l'antenne depuis la BD.
    Utilisée pour calculer la transition MRRW.

    Retourne un dict avec les métriques simulées, ou None.
    """
    cur = conn.cursor()
    cur.execute("""
        SELECT cpu, signal, latence, disponibilite
        FROM mesures
        WHERE antenne_id = %s
        ORDER BY date_mesure DESC
        LIMIT 1
    """, (antenne_id,))
    row = cur.fetchone()
    cur.close()

    if row and all(v is not None for v in row):
        return {
            "cpu":    float(row[0]),
            "signal": float(row[1]),
            "lat":    float(row[2]),
            "dispo":  float(row[3]),
        }
    return None


@iot_bp.route("/iot/mesure", methods=["POST"])
def recevoir_mesure_iot():
    """
    Reçoit une mesure JSON depuis l'Arduino Uno via serial_bridge.py.

    Body JSON :
    {
        "antenne_id":  121,
        "temperature": 28.5   ← température RÉELLE du capteur DHT11
    }

    Header requis : X-API-Key: esp32-noc-secret-2026

    Traitement :
      1. Valider la clé API et les données
      2. Lire la mesure précédente (pour MRRW)
      3. Simuler CPU/signal/latence/dispo en MRRW (même algo que le simulateur)
      4. Insérer en base (temp réelle + métriques simulées)
      5. Déclencher l'analyse IA ciblée UNIQUEMENT sur ISET Mahdia
         (force_no_retrain=True : le modèle ne se réentraîne pas)

    Règle : les autres antennes NE SONT PAS recalculées lors d'une mesure IoT.
    """
    # Vérification de la clé API
    if not verifier_cle(request):
        return jsonify({"error": "Clé API invalide ou manquante"}), 401

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Body JSON manquant"}), 400

    antenne_id  = data.get("antenne_id")
    temperature = data.get("temperature")

    if antenne_id is None or temperature is None:
        return jsonify({"error": "Champs requis : antenne_id, temperature"}), 400

    try:
        temperature = float(temperature)
        antenne_id  = int(antenne_id)
    except (ValueError, TypeError) as e:
        return jsonify({"error": f"Valeur invalide : {e}"}), 400

    print("[IOT] Mesure reçue :", antenne_id, temperature)

    # Validation plage DHT11 (0°C à 60°C — plage physique du capteur)
    if not (0.0 <= temperature <= 60.0):
        return jsonify({
            "error": f"Température DHT11 hors plage : {temperature:.1f}°C "
                     f"(plage acceptée : 0°C à 60°C)"
        }), 400

    try:
        conn = connecter_base_de_donnees()
        cur  = conn.cursor()

        # Vérifier que l'antenne existe en BD
        cur.execute("SELECT id, nom FROM antennes WHERE id = %s", (antenne_id,))
        antenne = cur.fetchone()
        if not antenne:
            cur.close(); conn.close()
            return jsonify({"error": f"Antenne ID {antenne_id} introuvable en base"}), 404

        # Lire la mesure précédente pour la transition MRRW
        prev = _lire_mesure_precedente(conn, antenne_id)

        # ── Calculer CPU / signal / latence / dispo (MRRW) ──────────
        if prev:
            # Transition douce depuis la mesure précédente
            cpu           = _mrrw(prev["cpu"],    PROFIL_ISET["cpu"])
            signal        = _mrrw(prev["signal"],  PROFIL_ISET["signal"])
            latence       = _mrrw(prev["lat"],     PROFIL_ISET["latence"])
            disponibilite = _mrrw(prev["dispo"],   PROFIL_ISET["dispo"])
        else:
            # Première mesure : partir des valeurs cibles avec bruit minimal
            p = PROFIL_ISET
            cpu           = round(p["cpu"]["cible"]    + random.gauss(0, p["cpu"]["bruit"]),    2)
            signal        = round(p["signal"]["cible"] + random.gauss(0, p["signal"]["bruit"]), 2)
            latence       = round(p["latence"]["cible"]+ random.gauss(0, p["latence"]["bruit"]),2)
            disponibilite = round(p["dispo"]["cible"]  + random.gauss(0, p["dispo"]["bruit"]),  2)

        # Insérer la mesure (température DHT11 réelle + métriques simulées MRRW)
        cur.execute("""
            INSERT INTO mesures
                (antenne_id, temperature, cpu, signal, latence, disponibilite,
                 statut, date_mesure)
            VALUES (%s, %s, %s, %s, %s, %s, 'analyse_ia_en_cours', %s)
        """, (
            antenne_id,
            round(temperature, 1),
            round(cpu, 1),
            round(signal, 1),
            round(latence, 1),
            round(disponibilite, 1),
            datetime.now()
        ))
        conn.commit()
        cur.close(); conn.close()

        print(
            f"[IoT] {antenne[1]} (ID={antenne_id}) — "
            f"Temp={temperature:.1f}°C (DHT11 réel) | "
            f"CPU={cpu:.1f}% | Signal={signal:.1f}dBm | "
            f"Latence={latence:.1f}ms | Dispo={disponibilite:.1f}%"
        )

    except Exception as e:
        print(f"[IoT ERREUR] {e}")
        return jsonify({"error": str(e)}), 500

    # ── Analyse IA ciblée UNIQUEMENT sur ISET Mahdia ─────────────
    # force_no_retrain=True : le modèle NE SE RÉENTRAÎNE PAS
    # Les autres antennes gardent leur statut INCHANGÉ
    try:
        from ia.prediction import run_ai_prediction

        response = run_ai_prediction(antenne_id=antenne_id, force_no_retrain=True)
        data_ia  = response.get_json()

        statut_ia   = "en_cours"
        risque_ia   = 0.0
        anomalie_ia = False

        if isinstance(data_ia, list) and data_ia:
            r           = data_ia[0]
            statut_ia   = r.get("statut",     "en_cours")
            risque_ia   = r.get("risk_score", 0.0)
            anomalie_ia = r.get("anomalie_if", False)

        print(
            f"[IoT] IA → {antenne[1]} : statut={statut_ia} | "
            f"score={risque_ia:.1f} | anomalie={anomalie_ia}"
        )

    except Exception as e:
        # La mesure est en base même si l'IA a échoué
        print(f"[IoT] IA non disponible : {e}")
        statut_ia = "en_cours"
        risque_ia = 0.0

    return jsonify({
        "success":       True,
        "message":       f"Mesure IoT reçue pour {antenne[1]}",
        "antenne_id":    antenne_id,
        "temperature":   temperature,
        "cpu":           cpu,
        "signal":        signal,
        "latence":       latence,
        "disponibilite": disponibilite,
        "statut_ia":     statut_ia,
        "risk_score":    risque_ia,
        "timestamp":     datetime.now().isoformat()
    }), 201


@iot_bp.route("/iot/status", methods=["GET"])
def iot_status():
    """Vérifie que la passerelle IoT est active."""
    return jsonify({
        "status":    "online",
        "service":   "GEO-TÉLÉCOM NOC IoT Gateway",
        "version":   "2.1",
        "metriques": ["temperature (DHT11 réel)", "cpu (MRRW)", "signal (MRRW)",
                      "latence (MRRW)", "disponibilite (MRRW)"],
        "timestamp": datetime.now().isoformat()
    })


@iot_bp.route("/iot/antenne/dernieres/<int:ant_id>", methods=["GET"])
def dernieres_mesures_iot(ant_id):
    """Retourne les 10 dernières mesures d'une antenne (debug Arduino)."""
    if not verifier_cle(request):
        return jsonify({"error": "Clé API invalide"}), 401
    try:
        conn = connecter_base_de_donnees()
        cur  = conn.cursor()
        cur.execute("""
            SELECT temperature, cpu, signal, latence, disponibilite,
                   statut, risk_score,
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


@iot_bp.route("/iot/antenne/lookup", methods=["GET"])
def lookup_antenne_par_nom():
    """
    Retourne l'identifiant d'une antenne à partir de son nom.

    Usage : GET /iot/antenne/lookup?nom=ISET+Mahdia
    Header requis : X-API-Key: esp32-noc-secret-2026

    Si l'antenne n'existe pas et que les coordonnées sont fournies,
    elle est créée automatiquement :
    GET /iot/antenne/lookup?nom=ISET+Mahdia&create=1&lat=35.522473&lon=11.030388

    Utilisé par serial_bridge.py pour récupérer l'ID de l'antenne
    dynamiquement (sans le coder en dur dans le sketch Arduino).
    """
    if not verifier_cle(request):
        return jsonify({"error": "Clé API invalide ou manquante"}), 401

    nom = request.args.get("nom", "").strip()
    if not nom:
        return jsonify({"error": "Paramètre 'nom' requis"}), 400

    try:
        conn = connecter_base_de_donnees()
        cur  = conn.cursor()

        # Recherche par nom exact
        cur.execute("SELECT id, nom, zone FROM antennes WHERE nom = %s", (nom,))
        row = cur.fetchone()

        if row:
            cur.close(); conn.close()
            return jsonify({
                "id":    int(row[0]),
                "nom":   row[1],
                "zone":  row[2],
                "found": True,
            })

        # Antenne introuvable — création automatique si demandée
        create = request.args.get("create", "0") == "1"
        lat    = request.args.get("lat", type=float)
        lon    = request.args.get("lon", type=float)

        if create and lat is not None and lon is not None:
            cur.execute("""
                INSERT INTO antennes
                    (nom, zone, type, latitude, longitude, operateur,
                     date_installation, geom)
                VALUES (%s, 'Mahdia Nord', '4G', %s, %s, 'Tunisie Telecom',
                        CURRENT_DATE,
                        ST_SetSRID(ST_MakePoint(%s, %s), 4326))
                RETURNING id, nom, zone
            """, (nom, lat, lon, lon, lat))
            new = cur.fetchone()
            conn.commit()
            cur.close(); conn.close()
            print(f"[IoT] Antenne '{nom}' créée automatiquement — ID={new[0]}")
            return jsonify({
                "id":      int(new[0]),
                "nom":     new[1],
                "zone":    new[2],
                "found":   False,
                "created": True,
            }), 201

        cur.close(); conn.close()
        return jsonify({
            "found":   False,
            "message": f"Antenne '{nom}' introuvable. "
                       f"Ajoutez ?create=1&lat=35.522473&lon=11.030388 pour la créer."
        }), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500
