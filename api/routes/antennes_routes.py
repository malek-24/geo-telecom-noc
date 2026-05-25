"""
routes/antennes_routes.py — CRUD antennes, statistiques et dashboard
Métriques : temperature, cpu, signal, latence, disponibilite
"""
import time
from datetime import datetime
from flask import Blueprint, request, jsonify, g
import pandas as pd

from database.connection import connecter_base_de_donnees, rows_to_dicts
from utils.globals import ADMIN_LOGS
from auth.decorators import token_required, role_required


network_bp = Blueprint('network_bp', __name__)


# ════════════════════════════════════════════════════════════════
#  LISTE & DÉTAIL DES ANTENNES
# ════════════════════════════════════════════════════════════════

@network_bp.route("/antennes", methods=["GET"])
@token_required
def liste_antennes():
    """
    Retourne TOUTES les antennes avec leur dernière mesure.
    Métriques : temperature, cpu, signal, latence, disponibilite
    """
    try:
        conn = connecter_base_de_donnees()
        df   = pd.read_sql("""
            SELECT
                a.id, a.nom, a.zone, a.type,
                a.latitude, a.longitude,
                a.date_installation::text,
                COALESCE(m.temperature,   28.0) AS temperature,
                COALESCE(m.cpu,           40.0) AS cpu,
                COALESCE(m.signal,       -65.0) AS signal,
                COALESCE(m.signal,       -65.0) AS signal_strength,
                COALESCE(m.latence,       15.0) AS latence,
                COALESCE(m.disponibilite, 99.0) AS disponibilite,
                CASE
                    WHEN a.statut = 'maintenance' THEN 'maintenance'
                    ELSE COALESCE(m.statut, 'normal')
                END AS statut,
                COALESCE(m.risk_score, 0.0) AS risk_score,
                CASE WHEN COALESCE(m.statut,'') = 'critique' THEN true ELSE false END AS anomalie,
                to_char(m.date_mesure, 'YYYY-MM-DD"T"HH24:MI:SS"Z"') AS date_mesure
            FROM antennes a
            LEFT JOIN LATERAL (
                SELECT * FROM mesures
                WHERE antenne_id = a.id
                ORDER BY date_mesure DESC
                LIMIT 1
            ) m ON true
            ORDER BY a.id
        """, conn)
        conn.close()

        if not df.empty:
            df["network_state"] = df["statut"].map({
                "normal":   "Healthy",
                "alerte":   "Warning",
                "critique": "Anomaly detected",
            }).fillna("Healthy")

        return jsonify(df.to_dict(orient="records"))
    except Exception as e:
        print(f"[ERREUR] GET /antennes : {e}")
        return jsonify({"error": str(e)}), 500


@network_bp.route("/antennes/<int:ant_id>", methods=["GET"])
@token_required
def get_antenne(ant_id):
    """Retourne les détails complets d'une antenne par ID."""
    try:
        conn = connecter_base_de_donnees()
        df   = pd.read_sql("""
            SELECT
                a.id, a.nom, a.zone, a.type, a.operateur,
                a.latitude, a.longitude,
                a.date_installation::text,
                COALESCE(m.temperature,   28.0) AS temperature,
                COALESCE(m.cpu,           40.0) AS cpu,
                COALESCE(m.signal,       -65.0) AS signal,
                COALESCE(m.latence,       15.0) AS latence,
                COALESCE(m.disponibilite, 99.0) AS disponibilite,
                CASE
                    WHEN a.statut = 'maintenance' THEN 'maintenance'
                    ELSE COALESCE(m.statut, 'normal')
                END AS statut,
                COALESCE(m.risk_score, 0.0) AS risk_score,
                (m.date_mesure AT TIME ZONE 'Africa/Tunis')::text AS date_mesure
            FROM antennes a
            LEFT JOIN LATERAL (
                SELECT * FROM mesures
                WHERE antenne_id = a.id
                ORDER BY date_mesure DESC
                LIMIT 1
            ) m ON true
            WHERE a.id = %(ant_id)s
        """, conn, params={"ant_id": ant_id})
        conn.close()

        if df.empty:
            return jsonify({"error": "Antenne introuvable"}), 404
        return jsonify(df.iloc[0].to_dict())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@network_bp.route("/antennes/<int:ant_id>/mesures", methods=["GET"])
@token_required
def get_antenne_mesures(ant_id):
    """Retourne l'historique chronologique des mesures d'une antenne."""
    limit = request.args.get("limit", 120, type=int)
    try:
        conn = connecter_base_de_donnees()
        df   = pd.read_sql("""
            SELECT
                to_char(date_mesure, 'YYYY-MM-DD"T"HH24:MI:SS"Z"') AS ts,
                temperature, cpu, signal, latence, disponibilite,
                COALESCE(statut, 'normal') AS statut,
                COALESCE(risk_score, 0.0)  AS risk_score
            FROM mesures
            WHERE antenne_id = %(ant_id)s
            ORDER BY date_mesure DESC
            LIMIT %(limit)s
        """, conn, params={"ant_id": ant_id, "limit": limit})
        conn.close()
        df = df.iloc[::-1].reset_index(drop=True)
        return jsonify(df.to_dict(orient="records"))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@network_bp.route("/antennes/<int:ant_id>/incidents", methods=["GET"])
@token_required
def get_antenne_incidents(ant_id):
    """Retourne les incidents d'une antenne spécifique."""
    limit = request.args.get("limit", 10, type=int)
    try:
        conn = connecter_base_de_donnees()
        cur  = conn.cursor()
        cur.execute("""
            SELECT id, titre, description, statut, criticite,
                   source_detection, duree_minutes,
                   to_char(date_creation,  'YYYY-MM-DD"T"HH24:MI:SS"Z"') AS date_creation,
                   to_char(date_resolution,'YYYY-MM-DD"T"HH24:MI:SS"Z"') AS date_resolution
            FROM incidents
            WHERE antenne_id = %s
            ORDER BY date_creation DESC
            LIMIT %s
        """, (ant_id, limit))
        data = rows_to_dicts(cur)
        cur.close(); conn.close()
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ════════════════════════════════════════════════════════════════
#  STATISTIQUES & DASHBOARD
# ════════════════════════════════════════════════════════════════

@network_bp.route("/stats", methods=["GET"])
@token_required
def stats_globales():
    """Retourne les statistiques globales du réseau."""
    try:
        conn = connecter_base_de_donnees()
        cur  = conn.cursor()

        cur.execute("SELECT COUNT(*) FROM antennes")
        total = cur.fetchone()[0]

        cur.execute("SELECT statut, COUNT(*) FROM antennes_statut GROUP BY statut")
        by_status = dict(cur.fetchall())

        cur.execute("""
            SELECT AVG(disponibilite), AVG(latence), AVG(cpu),
                   AVG(temperature),  AVG(signal)
            FROM antennes_statut
        """)
        avg = cur.fetchone()

        cur.execute("SELECT COUNT(*) FROM incidents WHERE statut != 'resolu'")
        incidents_actifs = cur.fetchone()[0]

        cur.close(); conn.close()

        return jsonify({
            "total_antennes":        total,
            "en_ligne":              by_status.get("normal",      0),
            "alertes":               by_status.get("alerte",      0),
            "critique":              by_status.get("critique",    0),
            "maintenance":           by_status.get("maintenance", 0),
            "disponibilite_globale": round(float(avg[0] or 100), 2),
            "latence_moyenne":       round(float(avg[1] or 0),   2),
            "cpu_moyen":             round(float(avg[2] or 0),   2),
            "temperature_moyenne":   round(float(avg[3] or 0),   2),
            "signal_moyen":          round(float(avg[4] or -65), 2),
            "incidents_actifs":      incidents_actifs,
            "antennes_actives":      total - by_status.get("maintenance", 0),
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@network_bp.route("/dashboard/summary", methods=["GET"])
@token_required
def get_dashboard_summary():
    """KPIs centralisés pour le tableau de bord principal."""
    try:
        conn = connecter_base_de_donnees()
        cur  = conn.cursor()

        cur.execute("SELECT COUNT(*) FROM antennes")
        total_antennes = cur.fetchone()[0]

        cur.execute("SELECT statut, COUNT(*) FROM antennes_statut GROUP BY statut")
        by_status   = dict(cur.fetchall())
        nb_critique = by_status.get("critique", 0)
        nb_alerte   = by_status.get("alerte",   0)
        nb_normal   = by_status.get("normal",   0)

        cur.execute("""
            SELECT AVG(disponibilite), AVG(cpu), AVG(latence), AVG(risk_score)
            FROM antennes_statut
        """)
        avg = cur.fetchone()

        cur.execute("SELECT COUNT(*) FROM incidents WHERE statut != 'resolu'")
        incidents_actifs = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM incidents WHERE statut != 'resolu' AND criticite = 'critical'")
        incidents_critiques = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM incidents WHERE statut != 'resolu' AND criticite = 'warning'")
        incidents_alertes = cur.fetchone()[0]

        cur.close(); conn.close()

        ai_risk_score = 0.0
        ai_confidence = 100.0
        if total_antennes > 0:
            ai_risk_score = min(100.0, ((nb_critique * 3 + nb_alerte) / total_antennes) * 100)
            ai_confidence = (nb_normal / total_antennes) * 100

        return jsonify({
            "total_antennes":   total_antennes,
            "en_ligne":         nb_normal,
            "alertes":          nb_alerte,
            "critique":         nb_critique,
            "availability":     round(float(avg[0] or 100), 2),
            "cpu_moyen":        round(float(avg[1] or 0),   2),
            "latence_moyenne":  round(float(avg[2] or 0),   2),
            "incidents_actifs": incidents_actifs,
            "active_alerts":    incidents_alertes,
            "incidents":        incidents_critiques,
            "anomalies":        nb_critique + nb_alerte,
            "ai_risk_score":    round(ai_risk_score, 1),
            "ai_confidence":    round(ai_confidence, 1),
        })
    except Exception as e:
        print(f"[ERREUR] GET /dashboard/summary : {e}")
        return jsonify({"error": str(e)}), 500


@network_bp.route("/dashboard/history", methods=["GET"])
@token_required
def get_dashboard_history():
    """Historique des KPIs réseau pour le graphique du dashboard."""
    try:
        conn = connecter_base_de_donnees()
        cur  = conn.cursor()
        cur.execute("""
            SELECT
                to_char(
                    date_trunc('hour', date_mesure) +
                    (EXTRACT(MINUTE FROM date_mesure)::int / 30)
                        * INTERVAL '30 minutes',
                    'HH24:MI'
                ) AS time,
                ROUND(AVG(cpu)::NUMERIC,          1) AS cpu,
                ROUND(AVG(disponibilite)::NUMERIC, 1) AS disponibilite,
                ROUND(AVG(latence)::NUMERIC,       1) AS latence,
                ROUND(AVG(signal)::NUMERIC,        1) AS signal,
                COUNT(*) FILTER (WHERE statut = 'alerte')   AS alertes,
                COUNT(*) FILTER (WHERE statut = 'critique') AS critiques
            FROM mesures
            WHERE date_mesure >= NOW() - INTERVAL '12 hours'
            GROUP BY 1
            ORDER BY 1 ASC
            LIMIT 24
        """)
        rows = rows_to_dicts(cur)
        cur.close(); conn.close()

        for r in rows:
            nb_a = int(r.get("alertes",   0) or 0)
            nb_c = int(r.get("critiques", 0) or 0)
            r["risque"]    = round(min(100, (nb_a + nb_c) * 2.5), 1)
            r["alertes"]   = nb_a
            r["critiques"] = nb_c

        return jsonify(rows)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ════════════════════════════════════════════════════════════════
#  CRUD ANTENNES
# ════════════════════════════════════════════════════════════════

@network_bp.route("/antennes", methods=["POST"])
@role_required('administrateur', 'ingenieur_reseau')
def creer_antenne():
    """Crée une nouvelle antenne avec une mesure initiale normale."""
    data     = request.get_json() or {}
    required = ['nom', 'zone', 'type', 'latitude', 'longitude']
    for field in required:
        if field not in data:
            return jsonify({"error": f"Champ manquant : {field}"}), 400

    try:
        conn = connecter_base_de_donnees()
        cur  = conn.cursor()
        lat  = float(data['latitude'])
        lon  = float(data['longitude'])
        nom  = data['nom'].strip()
        statut_initial = data.get('statut', 'normal')

        cur.execute("""
            INSERT INTO antennes
                (nom, zone, type, latitude, longitude, operateur, statut,
                 date_installation, geom)
            VALUES (%s, %s, %s, %s, %s, %s, %s, CURRENT_DATE,
                    ST_SetSRID(ST_MakePoint(%s, %s), 4326))
            RETURNING id
        """, (
            nom, data['zone'], data['type'], lat, lon,
            data.get('operateur', 'Tunisie Telecom'),
            statut_initial, lon, lat
        ))
        new_id = cur.fetchone()[0]

        # Mesure initiale (valeurs normales)
        cur.execute("""
            INSERT INTO mesures
                (antenne_id, temperature, cpu, signal, latence, disponibilite, statut, date_mesure)
            VALUES (%s, 28.0, 40.0, -65.0, 15.0, 99.0, %s, NOW())
        """, (new_id, statut_initial))

        conn.commit(); cur.close(); conn.close()

        ADMIN_LOGS.insert(0, {
            "id":          int(time.time()),
            "heure":       datetime.now().strftime("%Y-%m-%d %H:%M"),
            "utilisateur": g.current_user["username"],
            "action":      f"Création antenne {nom} (ID={new_id})",
            "statut":      "Succès"
        })
        return jsonify({"success": True, "id": new_id,
                        "message": f"Antenne {nom} créée avec succès."}), 201
    except Exception as e:
        print(f"[ERREUR] POST /antennes : {e}")
        return jsonify({"error": str(e)}), 500


@network_bp.route("/antennes/<int:ant_id>", methods=["PUT"])
@role_required('administrateur', 'ingenieur_reseau')
def modifier_antenne(ant_id):
    """Modifie les informations d'une antenne existante."""
    data    = request.get_json() or {}
    allowed = ['nom', 'zone', 'type', 'latitude', 'longitude', 'operateur', 'statut']
    fields  = []; values = []

    for key in allowed:
        if key in data:
            fields.append(f"{key} = %s")
            values.append(data[key])

    if 'latitude' in data and 'longitude' in data:
        fields.append("geom = ST_SetSRID(ST_MakePoint(%s, %s), 4326)")
        values.extend([float(data['longitude']), float(data['latitude'])])

    if not fields:
        return jsonify({"success": True, "message": "Rien à modifier."})

    values.append(ant_id)
    try:
        conn = connecter_base_de_donnees()
        cur  = conn.cursor()
        cur.execute(f"UPDATE antennes SET {', '.join(fields)} WHERE id = %s", tuple(values))
        if cur.rowcount == 0:
            cur.close(); conn.close()
            return jsonify({"error": "Antenne introuvable"}), 404
        conn.commit(); cur.close(); conn.close()

        ADMIN_LOGS.insert(0, {
            "id":          int(time.time()),
            "heure":       datetime.now().strftime("%Y-%m-%d %H:%M"),
            "utilisateur": g.current_user["username"],
            "action":      f"Modification antenne ID {ant_id}",
            "statut":      "Succès"
        })
        return jsonify({"success": True, "message": f"Antenne {ant_id} mise à jour."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@network_bp.route("/antennes/<int:ant_id>", methods=["DELETE"])
@role_required('administrateur')
def supprimer_antenne(ant_id):
    """Supprime une antenne et toutes ses données liées."""
    try:
        conn = connecter_base_de_donnees()
        cur  = conn.cursor()
        cur.execute("DELETE FROM incidents WHERE antenne_id = %s", (ant_id,))
        cur.execute("DELETE FROM mesures   WHERE antenne_id = %s", (ant_id,))
        cur.execute("DELETE FROM antennes  WHERE id = %s",         (ant_id,))
        if cur.rowcount == 0:
            cur.close(); conn.close()
            return jsonify({"error": "Antenne introuvable"}), 404
        conn.commit(); cur.close(); conn.close()

        ADMIN_LOGS.insert(0, {
            "id":          int(time.time()),
            "heure":       datetime.now().strftime("%Y-%m-%d %H:%M"),
            "utilisateur": g.current_user["username"],
            "action":      f"Suppression antenne ID {ant_id}",
            "statut":      "Succès"
        })
        return jsonify({"success": True, "message": f"Antenne {ant_id} supprimée."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ════════════════════════════════════════════════════════════════
#  MODIFICATION MANUELLE DES MÉTRIQUES (ADMIN — DÉMONSTRATION)
# ════════════════════════════════════════════════════════════════

@network_bp.route("/antennes/<int:ant_id>/metriques", methods=["PUT"])
@role_required('administrateur')
def modifier_metriques_antenne(ant_id):
    """
    [ADMIN] Modifie manuellement les métriques d'une antenne.

    Scénario de démonstration jury :
      1. L'admin saisit de nouvelles valeurs (ex: CPU=95%, Signal=-110dBm)
      2. Une nouvelle mesure est insérée en base immédiatement
      3. L'IA Isolation Forest analyse UNIQUEMENT cette antenne
         (les autres antennes ne sont pas recalculées)
      4. Le nouveau statut est retourné immédiatement

    Règle : force_no_retrain=True
      → Le modèle IA ne se réentraîne PAS lors d'une modification admin.
      → Il prédit uniquement, sur le modèle déjà en mémoire.

    Body JSON attendu :
    {
        "temperature":   95.0,
        "cpu":           95.0,
        "signal":       -110.0,
        "latence":       250.0,
        "disponibilite": 70.0
    }
    """
    data = request.get_json() or {}

    metriques_requises = ["temperature", "cpu", "signal", "latence", "disponibilite"]
    for champ in metriques_requises:
        if champ not in data:
            return jsonify({"error": f"Champ manquant : {champ}"}), 400

    try:
        temperature   = float(data["temperature"])
        cpu           = float(data["cpu"])
        signal        = float(data["signal"])
        latence       = float(data["latence"])
        disponibilite = float(data["disponibilite"])
    except (ValueError, TypeError) as e:
        return jsonify({"error": f"Valeur invalide : {e}"}), 400

    try:
        conn = connecter_base_de_donnees()
        cur  = conn.cursor()

        # Vérifier que l'antenne existe
        cur.execute("SELECT id, nom FROM antennes WHERE id = %s", (ant_id,))
        antenne = cur.fetchone()
        if not antenne:
            cur.close(); conn.close()
            return jsonify({"error": f"Antenne ID {ant_id} introuvable"}), 404

        # Insérer la nouvelle mesure avec les valeurs de l'admin
        cur.execute("""
            INSERT INTO mesures
                (antenne_id, temperature, cpu, signal, latence, disponibilite,
                 statut, date_mesure)
            VALUES (%s, %s, %s, %s, %s, %s, 'analyse_ia_en_cours', NOW())
        """, (
            ant_id,
            round(temperature, 1), round(cpu, 1), round(signal, 1),
            round(latence, 1), round(disponibilite, 1),
        ))
        conn.commit()
        cur.close(); conn.close()

        # Journaliser l'action admin
        ADMIN_LOGS.insert(0, {
            "id":          int(time.time()),
            "heure":       datetime.now().strftime("%Y-%m-%d %H:%M"),
            "utilisateur": g.current_user["username"],
            "action":      (
                f"Modification métriques {antenne[1]} (ID={ant_id}) — "
                f"Temp={temperature}°C CPU={cpu}% Signal={signal}dBm "
                f"Latence={latence}ms Dispo={disponibilite}%"
            ),
            "statut": "Succès"
        })

    except Exception as e:
        print(f"[ERREUR] PUT /antennes/{ant_id}/metriques : {e}")
        return jsonify({"error": str(e)}), 500

    # ── Analyse IA ciblée sur cette antenne uniquement ──────────────
    # force_no_retrain=True : le modèle NE SE RÉENTRAÎNE PAS
    # Il prédit uniquement, sur le modèle déjà en mémoire
    try:
        from ia.prediction import run_ai_prediction

        # Appel direct Python (plus rapide et plus fiable qu'un appel HTTP)
        response = run_ai_prediction(antenne_id=ant_id, force_no_retrain=True)

        # Extraire le résultat JSON
        data_ia = response.get_json()
        if isinstance(data_ia, list) and data_ia:
            r = data_ia[0]  # Résultat de cette antenne uniquement
            return jsonify({
                "success":    True,
                "message":    f"Métriques mises à jour pour {antenne[1]}. IA recalculée.",
                "antenne_id": ant_id,
                "statut":     r.get("statut",     "inconnu"),
                "risk_score": r.get("risk_score", 0),
            })

        # Cas rare : résultat vide (ne devrait pas arriver)
        return jsonify({
            "success":    True,
            "message":    f"Métriques mises à jour pour {antenne[1]}. IA déclenchée.",
            "antenne_id": ant_id,
        })

    except Exception as e:
        # L'insertion a réussi même si l'IA n'a pas répondu
        print(f"[IA ERREUR après modification admin] {e}")
        return jsonify({
            "success":    True,
            "message":    f"Métriques mises à jour pour {antenne[1]}. IA déclenchée (en cours).",
            "antenne_id": ant_id,
        })
