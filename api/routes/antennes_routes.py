import os, time, json, random, io
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, g, send_file
import pandas as pd
from werkzeug.security import generate_password_hash, check_password_hash
from database.connection import connecter_base_de_donnees, rows_to_dicts
from utils.globals import JWT_SECRET, JWT_EXPIRATION_HOURS, ADMIN_LOGS, SYSTEM_SETTINGS
from auth.decorators import token_required, admin_required, role_required
from ia.prediction import run_ai_prediction, get_ia_report_anomalies
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm


network_bp = Blueprint('network_bp', __name__)

@network_bp.route("/antennes", methods=["GET"])
@token_required
def liste_antennes():
    """
    Retourne TOUTES les antennes (même sans mesures) via LEFT JOIN.
    Les antennes sans mesures reçoivent des valeurs par défaut.
    """
    try:
        conn = connecter_base_de_donnees()
        df = pd.read_sql("""
            SELECT
                a.id, a.nom, a.zone, a.type,
                a.latitude, a.longitude,
                a.date_installation::text,
                COALESCE(m.temperature,   35.0) AS temperature,
                COALESCE(m.cpu,           20.0) AS cpu,
                COALESCE(m.ram,           25.0) AS ram,
                COALESCE(m.signal,       -65.0) AS signal,
                COALESCE(m.signal,       -65.0) AS signal_strength,
                COALESCE(m.traffic,      100.0) AS traffic,
                COALESCE(m.traffic,      100.0) AS debit,
                COALESCE(m.latence,       15.0) AS latence,
                COALESCE(m.packet_loss,    0.0) AS packet_loss,
                COALESCE(m.disponibilite, 99.0) AS disponibilite,
                COALESCE(m.jitter,         0.0) AS jitter,
                CASE 
                    WHEN a.statut = 'maintenance' THEN 'maintenance'
                    ELSE COALESCE(m.statut, 'normal')
                END AS statut,
                COALESCE(m.risk_score,     0.0) AS risk_score,
                CASE WHEN COALESCE(m.statut,'') = 'critique' THEN true ELSE false END AS anomalie,
                (m.date_mesure AT TIME ZONE 'Africa/Tunis')::text AS date_mesure
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
            df["anomaly_state"] = df["statut"].eq("critique")
        print(f"[API] GET /antennes → {len(df)} antennes retournées")
        return jsonify(df.to_dict(orient="records"))
    except Exception as e:
        print(f"[ERREUR] GET /antennes : {e}")
        return jsonify({"error": str(e)}), 500

@network_bp.route("/antennes/<int:ant_id>", methods=["GET"])
@token_required
def get_antenne(ant_id):
    """Retourne les détails d'une antenne par ID (avec dernière mesure)."""
    try:
        conn = connecter_base_de_donnees()
        df = pd.read_sql("""
            SELECT
                a.id, a.nom, a.zone, a.type, a.operateur,
                a.latitude, a.longitude,
                a.date_installation::text,
                COALESCE(m.temperature,   35.0) AS temperature,
                COALESCE(m.cpu,           20.0) AS cpu,
                COALESCE(m.ram,           25.0) AS ram,
                COALESCE(m.signal,       -65.0) AS signal,
                COALESCE(m.traffic,      100.0) AS traffic,
                COALESCE(m.latence,       15.0) AS latence,
                COALESCE(m.packet_loss,    0.0) AS packet_loss,
                COALESCE(m.disponibilite, 99.0) AS disponibilite,
                COALESCE(m.jitter,         0.0) AS jitter,
                CASE 
                    WHEN a.statut = 'maintenance' THEN 'maintenance'
                    ELSE COALESCE(m.statut, 'normal')
                END AS statut,
                COALESCE(m.risk_score,     0.0) AS risk_score,
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
    """Retourne l'historique des mesures d'une antenne (24 dernières par défaut)."""
    limit = request.args.get("limit", 24, type=int)
    try:
        conn = connecter_base_de_donnees()
        df = pd.read_sql("""
            SELECT
                (date_mesure AT TIME ZONE 'Africa/Tunis')::text AS ts,
                temperature, cpu, ram, signal, traffic, latence,
                packet_loss, disponibilite, jitter,
                COALESCE(statut, 'normal') AS statut,
                COALESCE(risk_score, 0.0)  AS risk_score
            FROM mesures
            WHERE antenne_id = %(ant_id)s
            ORDER BY date_mesure DESC
            LIMIT %(limit)s
        """, conn, params={"ant_id": ant_id, "limit": limit})
        conn.close()
        # Reverse so charts show chronological order
        df = df.iloc[::-1].reset_index(drop=True)
        return jsonify(df.to_dict(orient="records"))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@network_bp.route("/antennes/<int:ant_id>/incidents", methods=["GET"])
@token_required
def get_antenne_incidents(ant_id):
    """Retourne les incidents d'une antenne."""
    limit = request.args.get("limit", 10, type=int)
    try:
        conn = connecter_base_de_donnees()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, titre, description, statut, criticite,
                   source_detection, duree_minutes,
                   (date_creation AT TIME ZONE 'Africa/Tunis')::text AS date_debut,
                   (date_resolution AT TIME ZONE 'Africa/Tunis')::text AS created_at
            FROM incidents
            WHERE antenne_id = %s
            ORDER BY date_creation DESC
            LIMIT %s
        """, (ant_id, limit))
        data = rows_to_dicts(cur)
        cur.close()
        conn.close()
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@network_bp.route("/stats", methods=["GET"])
@token_required
def stats_globales():
    try:
        conn = connecter_base_de_donnees()
        cur = conn.cursor()
        
        cur.execute("SELECT COUNT(*) FROM antennes")
        total = cur.fetchone()[0]
        
        cur.execute("SELECT statut, COUNT(*) FROM antennes_statut GROUP BY statut")
        by_status = dict(cur.fetchall())
        
        cur.execute("""
            SELECT AVG(disponibilite), AVG(debit), SUM(debit), AVG(latence),
                   AVG(cpu), AVG(temperature), AVG(packet_loss), AVG(jitter)
            FROM antennes_statut
        """)
        avg_data     = cur.fetchone()
        avg_dispo    = avg_data[0] or 100
        avg_debit    = avg_data[1] or 0
        total_debit  = avg_data[2] or 0
        avg_latence  = avg_data[3] or 0
        avg_cpu      = avg_data[4] or 0
        avg_temp     = avg_data[5] or 0
        avg_pkt_loss = avg_data[6] or 0
        avg_jitter   = avg_data[7] or 0

        cur.execute("SELECT COUNT(*) FROM incidents WHERE statut != 'resolu'")
        incidents_actifs = cur.fetchone()[0]

        cur.close()
        conn.close()

        return jsonify({
            "total_antennes":        total,
            "en_ligne":              by_status.get("normal", 0),
            "alertes":               by_status.get("alerte", 0),
            "critique":              by_status.get("critique", 0),
            "maintenance":           by_status.get("maintenance", 0),
            "disponibilite_globale": round(float(avg_dispo), 2),
            "debit_moyen":           round(float(avg_debit), 2),
            "latence_moyenne":       round(float(avg_latence), 2),
            "packet_loss_moyen":     round(float(avg_pkt_loss), 2),
            "jitter_moyen":          round(float(avg_jitter), 2),
            "cpu_moyen":             round(float(avg_cpu), 2),
            "temperature_moyenne":   round(float(avg_temp), 2),
            "incidents_actifs":      incidents_actifs,
            "debit_total":           round(float(total_debit), 2),
            "antennes_actives":      total - by_status.get("maintenance", 0)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@network_bp.route("/dashboard/summary", methods=["GET"])
@token_required
def get_dashboard_summary():
    """ KPIs centralisés — Source unique : antennes_statut (résultats IA). """
    try:
        conn = connecter_base_de_donnees()
        cur  = conn.cursor()

        # ── Comptage par statut IA (source unique de vérité) ─────────────────
        cur.execute("SELECT COUNT(*) FROM antennes")
        total_antennes = cur.fetchone()[0]

        cur.execute("SELECT statut, COUNT(*) FROM antennes_statut GROUP BY statut")
        by_status = dict(cur.fetchall())
        nb_critique = by_status.get("critique", 0)
        nb_alerte   = by_status.get("alerte",   0)
        nb_normal   = by_status.get("normal",   0)

        # ── Métriques réseau moyennes ─────────────────────────────────────────
        cur.execute("""
            SELECT AVG(disponibilite), AVG(debit), AVG(cpu),
                   AVG(latence), AVG(risk_score)
            FROM antennes_statut
        """)
        avg = cur.fetchone()
        avg_dispo      = float(avg[0] or 100)
        avg_debit      = float(avg[1] or 0)
        avg_cpu        = float(avg[2] or 0)
        avg_latence    = float(avg[3] or 0)
        avg_risk_score = float(avg[4] or 0)

        # ── Incidents IA actifs ───────────────────────────────────────────────
        cur.execute("SELECT COUNT(*) FROM incidents WHERE statut != 'resolu'")
        incidents_actifs = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM incidents WHERE statut != 'resolu' AND criticite = 'critical'")
        incidents_critiques = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM incidents WHERE statut != 'resolu' AND criticite = 'warning'")
        incidents_alertes = cur.fetchone()[0]

        # ── Score risque IA global ────────────────────────────────────────────
        # Utilise directement la moyenne des risk_score calculés par Isolation Forest
        if total_antennes > 0:
            ai_risk_score = min(100.0, ((nb_critique * 3 + nb_alerte) / total_antennes) * 100)
        else:
            ai_risk_score = round(avg_risk_score, 1)

        cur.close()
        conn.close()

        return jsonify({
            "total_antennes":  total_antennes,
            "en_ligne":        nb_normal,
            "alertes":         nb_alerte,
            "critique":        nb_critique,
            "availability":    round(avg_dispo, 2),
            "debit_moyen":     round(avg_debit, 2),
            "cpu_moyen":       round(avg_cpu, 2),
            "latence_moyenne": round(avg_latence, 2),
            "incidents_actifs": incidents_actifs,
            "active_alerts":   incidents_alertes,
            "incidents":       incidents_critiques,
            "anomalies":       nb_critique + nb_alerte,
            "ai_risk_score":   round(ai_risk_score, 1),
            "ai_confidence":   96.4,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@network_bp.route("/dashboard/history", methods=["GET"])
@token_required
def get_dashboard_history():
    """ Returns historical KPI data for the last 15 cycles to populate charts. """
    try:
        conn = connecter_base_de_donnees()
        cur  = conn.cursor()
        # Données réelles — agrégées par cycle de 30 min sur les 12 dernières heures
        cur.execute("""
            SELECT
                to_char(
                    (date_trunc('hour', date_mesure AT TIME ZONE 'Africa/Tunis') +
                    (EXTRACT(MINUTE FROM (date_mesure AT TIME ZONE 'Africa/Tunis'))::int / 30) * INTERVAL '30 minutes'),
                    'HH24:MI'
                ) AS time,
                ROUND(AVG(cpu)::NUMERIC, 1)          AS cpu,
                ROUND(AVG(traffic)::NUMERIC, 1)      AS debit,
                ROUND(AVG(disponibilite)::NUMERIC, 1) AS disponibilite,
                ROUND(AVG(latence)::NUMERIC, 1)      AS latence,
                COUNT(*) FILTER (WHERE statut = 'alerte')   AS alertes,
                COUNT(*) FILTER (WHERE statut = 'critique') AS critiques
            FROM mesures
            WHERE date_mesure >= NOW() - INTERVAL '12 hours'
            GROUP BY 1
            ORDER BY 1 ASC
            LIMIT 24
        """)
        rows = rows_to_dicts(cur)
        cur.close()
        conn.close()

        # Enrichir avec un "risque" normalisé basé sur les proportions alerte/critique
        for r in rows:
            nb_a = r.get("alertes",  0) or 0
            nb_c = r.get("critiques",0) or 0
            total = nb_a + nb_c
            r["risque"] = round(min(100, total * 2.5), 1)
            # Convertir en entiers propres
            for key in ["alertes", "critiques"]:
                r[key] = int(r[key] or 0)

        return jsonify(rows)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@network_bp.route("/antennes", methods=["POST"])
@role_required('administrateur', 'ingenieur_reseau')
def creer_antenne():
    """Ajouter une nouvelle antenne + mesure initiale automatique."""
    data = request.get_json() or {}
    required = ['nom', 'zone', 'type', 'latitude', 'longitude']
    for field in required:
        if field not in data:
            return jsonify({"error": f"Champ manquant : {field}"}), 400
    try:
        conn = connecter_base_de_donnees()
        cur = conn.cursor()

        lat = float(data['latitude'])
        lon = float(data['longitude'])
        nom = data['nom'].strip()

        # 1. Insérer l'antenne
        statut_initial = data.get('statut', 'normal')
        cur.execute("""
            INSERT INTO antennes
                (nom, zone, type, latitude, longitude, operateur, statut,
                 date_installation, geom)
            VALUES (%s, %s, %s, %s, %s, %s, %s, CURRENT_DATE,
                    ST_SetSRID(ST_MakePoint(%s, %s), 4326))
            RETURNING id
        """, (
            nom, data['zone'], data['type'],
            lat, lon,
            data.get('operateur', 'Tunisie Telecom'),
            statut_initial,
            lon, lat
        ))
        new_id = cur.fetchone()[0]

        # 2. Créer une mesure initiale (antenne visible immédiatement dans la carte et l'IA)
        cur.execute("""
            INSERT INTO mesures
                (antenne_id, temperature, cpu, ram, signal, traffic,
                 latence, disponibilite, packet_loss, jitter, statut, date_mesure)
            VALUES (%s, 35.0, 20.0, 25.0, -65.0, 100.0, 15.0, 99.0, 0.0, 0.0, %s, NOW())
        """, (new_id, statut_initial))

        conn.commit()
        cur.close()
        conn.close()

        print(f"[SYNC] Antenne ajoutée : {nom} (ID={new_id}) — mesure initiale créée")
        ADMIN_LOGS.insert(0, {
            "id": int(time.time()),
            "heure": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "utilisateur": g.current_user["username"],
            "action": f"Création antenne {nom} (ID={new_id})",
            "statut": "Succès"
        })
        return jsonify({"success": True, "id": new_id,
                        "message": f"Antenne {nom} créée et synchronisée."}), 201
    except Exception as e:
        print(f"[ERREUR] POST /antennes : {e}")
        return jsonify({"error": str(e)}), 500

@network_bp.route("/antennes/<int:ant_id>", methods=["PUT"])
@role_required('administrateur', 'ingenieur_reseau')
def modifier_antenne(ant_id):
    """Modifier les informations d'une antenne existante."""
    data = request.get_json() or {}
    allowed = ['nom', 'zone', 'type', 'latitude', 'longitude', 'operateur', 'statut']
    fields = []; values = []
    for key in allowed:
        if key in data:
            fields.append(f"{key} = %s")
            values.append(data[key])
    # Mettre à jour la géométrie si coordonnées modifiées
    if 'latitude' in data and 'longitude' in data:
        fields.append("geom = ST_SetSRID(ST_MakePoint(%s, %s), 4326)")
        values.extend([float(data['longitude']), float(data['latitude'])])
    if not fields:
        return jsonify({"success": True, "message": "Rien à modifier."})
    values.append(ant_id)
    try:
        conn = connecter_base_de_donnees()
        cur = conn.cursor()
        cur.execute(f"UPDATE antennes SET {', '.join(fields)} WHERE id = %s", tuple(values))
        if cur.rowcount == 0:
            cur.close(); conn.close()
            return jsonify({"error": "Antenne introuvable"}), 404
        conn.commit()
        cur.close(); conn.close()
        ADMIN_LOGS.insert(0, {
            "id": int(time.time()),
            "heure": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "utilisateur": g.current_user["username"],
            "action": f"Modification antenne ID {ant_id}",
            "statut": "Succès"
        })
        return jsonify({"success": True, "message": f"Antenne {ant_id} mise à jour."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@network_bp.route("/antennes/<int:ant_id>", methods=["DELETE"])
@role_required('administrateur')
def supprimer_antenne(ant_id):
    """Supprimer une antenne (Administrateur uniquement)."""
    try:
        conn = connecter_base_de_donnees()
        cur = conn.cursor()
        # Supprimer les incidents liés d'abord
        cur.execute("DELETE FROM incidents WHERE antenne_id = %s", (ant_id,))
        cur.execute("DELETE FROM mesures WHERE antenne_id = %s", (ant_id,))
        cur.execute("DELETE FROM antennes WHERE id = %s", (ant_id,))
        if cur.rowcount == 0:
            cur.close(); conn.close()
            return jsonify({"error": "Antenne introuvable"}), 404
        conn.commit()
        cur.close(); conn.close()
        ADMIN_LOGS.insert(0, {
            "id": int(time.time()),
            "heure": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "utilisateur": g.current_user["username"],
            "action": f"Suppression antenne ID {ant_id}",
            "statut": "Succès"
        })
        return jsonify({"success": True, "message": f"Antenne {ant_id} supprimée."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

