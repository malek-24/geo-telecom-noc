"""
routes/incidents_routes.py — Gestion des incidents et alertes IA
Expose les endpoints REST pour les incidents, les commentaires,
les alertes temps réel et les activités de modération.
"""
from datetime import datetime
from flask import Blueprint, request, jsonify, g

from database.connection import connecter_base_de_donnees, rows_to_dicts
from utils.globals import ADMIN_LOGS
from auth.decorators import token_required, role_required
from ia.prediction import run_ai_prediction


incidents_bp = Blueprint('incidents_bp', __name__)


# ════════════════════════════════════════════════════════════════
#  INCIDENTS
# ════════════════════════════════════════════════════════════════

@incidents_bp.route("/incidents", methods=["GET"])
@token_required
def list_incidents():
    """Retourne tous les incidents (actifs en premier), triés par date."""
    try:
        conn = connecter_base_de_donnees()
        cur  = conn.cursor()
        cur.execute("""
            SELECT
                i.id,
                'INC-' || LPAD(i.id::text, 4, '0') AS incident_id,
                i.antenne_id,
                a.nom  AS antenne,
                a.zone,
                i.titre,
                COALESCE(i.type_anomalie, i.titre) AS type_anomalie,
                i.description,
                i.statut,
                i.criticite,
                i.source_detection,
                i.metriques,
                i.duree_minutes,
                to_char(i.date_creation, 'YYYY-MM-DD"T"HH24:MI:SS"Z"') AS date_creation,
                to_char(i.date_resolution, 'YYYY-MM-DD"T"HH24:MI:SS"Z"') AS date_resolution
            FROM incidents i
            JOIN antennes a ON i.antenne_id = a.id
            ORDER BY
                CASE i.statut WHEN 'en_cours' THEN 0 ELSE 1 END,
                i.date_creation DESC
        """)
        data = rows_to_dicts(cur)
        cur.close(); conn.close()
        return jsonify(data)
    except Exception as e:
        print(f"[ERREUR] GET /incidents : {e}")
        return jsonify({"error": str(e)}), 500


@incidents_bp.route("/incidents/<int:incident_id>", methods=["GET"])
@token_required
def incident_details(incident_id):
    """Retourne le détail d'un incident par son ID."""
    try:
        conn = connecter_base_de_donnees()
        cur  = conn.cursor()
        cur.execute("""
            SELECT
                i.id,
                'INC-' || LPAD(i.id::text, 4, '0') AS incident_id,
                i.antenne_id,
                a.nom  AS antenne,
                a.zone,
                i.titre,
                COALESCE(i.type_anomalie, i.titre) AS type_anomalie,
                i.description,
                i.statut,
                i.criticite,
                i.source_detection,
                i.metriques,
                i.duree_minutes,
                to_char(i.date_creation, 'YYYY-MM-DD"T"HH24:MI:SS"Z"') AS date_creation,
                to_char(i.date_resolution, 'YYYY-MM-DD"T"HH24:MI:SS"Z"') AS date_resolution
            FROM incidents i
            JOIN antennes a ON i.antenne_id = a.id
            WHERE i.id = %s
        """, (incident_id,))
        row = cur.fetchone()
        if not row:
            cur.close(); conn.close()
            return jsonify({"error": "Incident introuvable"}), 404
        cols = [d[0] for d in cur.description]
        cur.close(); conn.close()
        return jsonify(dict(zip(cols, row)))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@incidents_bp.route("/incidents/<int:incident_id>/resolve", methods=["POST", "PUT"])
@token_required
def resolve_incident(incident_id):
    """Marque un incident comme résolu et relance l'analyse IA."""
    try:
        conn = connecter_base_de_donnees()
        cur  = conn.cursor()
        cur.execute("""
            UPDATE incidents
            SET statut = 'resolu', date_resolution = NOW()
            WHERE id = %s
        """, (incident_id,))
        conn.commit()
        updated = cur.rowcount
        cur.close(); conn.close()

        if updated == 0:
            return jsonify({"error": "Incident introuvable"}), 404

        # Relancer l'IA pour mettre à jour le statut de l'antenne
        run_ai_prediction()
        return jsonify({"success": True, "id": incident_id, "statut": "resolu"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ════════════════════════════════════════════════════════════════
#  COMMENTAIRES
# ════════════════════════════════════════════════════════════════

@incidents_bp.route("/incidents/<int:incident_id>/commentaires", methods=["GET"])
@token_required
def get_commentaires(incident_id):
    """Retourne les commentaires d'un incident."""
    try:
        conn = connecter_base_de_donnees()
        cur  = conn.cursor()
        cur.execute("""
            SELECT id, incident_id, utilisateur_nom, role, contenu,
                   statut_validation, etat_resolution,
                   (date_creation AT TIME ZONE 'Africa/Tunis')::text AS date_creation
            FROM commentaires_incidents
            WHERE incident_id = %s
            ORDER BY date_creation ASC
        """, (incident_id,))
        data = rows_to_dicts(cur)
        cur.close(); conn.close()
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@incidents_bp.route("/incidents/<int:incident_id>/commentaires", methods=["POST"])
@role_required('administrateur', 'ingenieur_reseau', 'technicien_terrain')
def post_commentaire(incident_id):
    """Ajoute un commentaire à un incident."""
    data    = request.get_json() or {}
    contenu = data.get("contenu", "").strip()
    if not contenu:
        return jsonify({"error": "Commentaire vide"}), 400

    utilisateur_nom = g.current_user["username"]
    role            = g.current_user["role"]
    utilisateur_id  = g.current_user.get("id")
    statut_validation = "validé" if role == "administrateur" else "en attente"
    etat_resolution   = data.get("etat_resolution", "en_cours")

    try:
        conn = connecter_base_de_donnees()
        cur  = conn.cursor()

        # Vérifier que l'incident existe
        cur.execute("SELECT id FROM incidents WHERE id = %s", (incident_id,))
        if not cur.fetchone():
            cur.close(); conn.close()
            return jsonify({"error": "Incident introuvable"}), 404

        cur.execute("""
            INSERT INTO commentaires_incidents
                (incident_id, utilisateur_id, utilisateur_nom, role, contenu, statut_validation, etat_resolution)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (incident_id, utilisateur_id, utilisateur_nom, role, contenu, statut_validation, etat_resolution))
        conn.commit()
        new_id = cur.fetchone()[0]

        # Si marqué résolu via le commentaire
        if etat_resolution in ('réglé', 'resolu'):
            cur.execute("UPDATE incidents SET statut = 'resolu', date_resolution = NOW() WHERE id = %s", (incident_id,))
            conn.commit()
            run_ai_prediction()

        cur.close(); conn.close()
        return jsonify({"success": True, "id": new_id, "statut_validation": statut_validation})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@incidents_bp.route("/commentaires/<int:comment_id>/resolution", methods=["PUT"])
@token_required
def changer_etat_resolution(comment_id):
    """Met à jour l'état de résolution d'un commentaire."""
    data        = request.get_json() or {}
    nouvel_etat = data.get("etat_resolution")
    if not nouvel_etat:
        return jsonify({"error": "État manquant"}), 400

    try:
        conn = connecter_base_de_donnees()
        cur  = conn.cursor()
        cur.execute("""
            UPDATE commentaires_incidents
            SET etat_resolution = %s
            WHERE id = %s
            RETURNING incident_id
        """, (nouvel_etat, comment_id))
        row = cur.fetchone()
        if row and nouvel_etat in ('réglé', 'resolu'):
            cur.execute("UPDATE incidents SET statut = 'resolu', date_resolution = NOW() WHERE id = %s", (row[0],))
            run_ai_prediction()
        conn.commit()
        cur.close(); conn.close()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@incidents_bp.route("/commentaires/<int:comment_id>/valider", methods=["PUT"])
@token_required
def valider_commentaire(comment_id):
    """Valide un commentaire en attente (Administrateur uniquement)."""
    if g.current_user["role"] != "administrateur":
        return jsonify({"error": "Non autorisé"}), 403
    try:
        conn = connecter_base_de_donnees()
        cur  = conn.cursor()
        cur.execute("UPDATE commentaires_incidents SET statut_validation = 'validé' WHERE id = %s", (comment_id,))
        conn.commit()
        cur.close(); conn.close()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@incidents_bp.route("/commentaires/<int:comment_id>", methods=["DELETE"])
@token_required
def supprimer_commentaire(comment_id):
    """Supprime un commentaire (Administrateur uniquement)."""
    if g.current_user["role"] != "administrateur":
        return jsonify({"error": "Non autorisé"}), 403
    try:
        conn = connecter_base_de_donnees()
        cur  = conn.cursor()
        cur.execute("DELETE FROM commentaires_incidents WHERE id = %s", (comment_id,))
        conn.commit()
        cur.close(); conn.close()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ════════════════════════════════════════════════════════════════
#  ALERTES TEMPS RÉEL
# ════════════════════════════════════════════════════════════════

@incidents_bp.route("/alerts", methods=["GET"])
@token_required
def list_alerts():
    """
    Retourne les antennes en alerte ou critique (max 12).
    Utilisé par la page des alertes et la carte.
    """
    try:
        import pandas as pd
        conn = connecter_base_de_donnees()
        df   = pd.read_sql("""
            SELECT id, nom, zone, type,
                   temperature, cpu, ram, signal, debit,
                   latence, packet_loss, disponibilite,
                   statut, risk_score,
                   date_mesure::text
            FROM antennes_statut
            WHERE statut IN ('alerte', 'critique')
            ORDER BY
                CASE statut WHEN 'critique' THEN 0 ELSE 1 END,
                risk_score DESC
            LIMIT 12
        """, conn)
        conn.close()
        return jsonify(df.to_dict(orient="records"))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@incidents_bp.route("/alerts/critical", methods=["GET"])
@token_required
def list_critical_alerts():
    """
    ⚡ ROUTE CRITIQUE — Utilisée par CriticalAlertBanner.js pour les popups temps réel.
    Retourne les INCIDENTS actifs de criticité 'critical' avec les infos de l'antenne.
    """
    try:
        conn = connecter_base_de_donnees()
        cur  = conn.cursor()
        cur.execute("""
            SELECT
                i.id,
                i.antenne_id,
                a.nom,
                a.zone,
                i.titre,
                i.type_anomalie,
                i.criticite,
                to_char(i.date_creation, 'YYYY-MM-DD"T"HH24:MI:SS"Z"') AS date_creation
            FROM incidents i
            JOIN antennes a ON i.antenne_id = a.id
            WHERE i.statut = 'en_cours'
              AND i.criticite = 'critical'
            ORDER BY i.date_creation DESC
            LIMIT 5
        """)
        data = rows_to_dicts(cur)
        cur.close(); conn.close()
        return jsonify(data)
    except Exception as e:
        print(f"[ERREUR] GET /alerts/critical : {e}")
        return jsonify({"error": str(e)}), 500


# ════════════════════════════════════════════════════════════════
#  MODÉRATION
# ════════════════════════════════════════════════════════════════

@incidents_bp.route("/admin/commentaires", methods=["GET"])
@token_required
def get_all_commentaires_en_attente():
    """Liste tous les commentaires en attente de validation (Admin uniquement)."""
    if g.current_user["role"] != "administrateur":
        return jsonify({"error": "Non autorisé"}), 403
    try:
        conn = connecter_base_de_donnees()
        cur  = conn.cursor()
        cur.execute("""
            SELECT c.id, c.incident_id, c.utilisateur_nom, c.role,
                   c.contenu, c.statut_validation, c.etat_resolution,
                   to_char(c.date_creation, 'YYYY-MM-DD"T"HH24:MI:SS"Z"') AS date_creation,
                   i.titre AS incident_titre
            FROM commentaires_incidents c
            JOIN incidents i ON c.incident_id = i.id
            WHERE c.statut_validation = 'en attente'
            ORDER BY c.date_creation DESC
        """)
        data = rows_to_dicts(cur)
        cur.close(); conn.close()
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@incidents_bp.route("/moderation/activity", methods=["GET"])
@token_required
def get_moderation_activity():
    """Retourne l'historique récent des incidents pour le panel modération."""
    try:
        conn = connecter_base_de_donnees()
        cur  = conn.cursor()
        cur.execute("""
            SELECT
                i.id,
                to_char(i.date_creation AT TIME ZONE 'Africa/Tunis', 'HH24:MI') AS time,
                i.titre AS text,
                i.criticite AS type,
                a.nom AS antenne
            FROM incidents i
            JOIN antennes a ON i.antenne_id = a.id
            ORDER BY i.date_creation DESC
            LIMIT 10
        """)
        data = rows_to_dicts(cur)
        cur.close(); conn.close()
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@incidents_bp.route("/moderation/users", methods=["GET"])
@token_required
def get_moderation_users():
    """Liste des utilisateurs pour le panel de modération."""
    try:
        conn = connecter_base_de_donnees()
        cur  = conn.cursor()
        cur.execute("""
            SELECT id, username AS nom, role, status AS statut, 0 AS actions
            FROM users
            ORDER BY id ASC
            LIMIT 20
        """)
        data = rows_to_dicts(cur)
        cur.close(); conn.close()
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@incidents_bp.route("/moderation/action", methods=["POST"])
@token_required
def moderation_action():
    """Traite une action de modération (générique)."""
    data   = request.get_json() or {}
    action = data.get("action", "")
    return jsonify({"success": True, "message": f"Action '{action}' traitée avec succès."})
