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


incidents_bp = Blueprint('incidents_bp', __name__)

@incidents_bp.route("/incidents", methods=["GET"])
@token_required
def list_incidents():
    try:
        conn = connecter_base_de_donnees()
        cur = conn.cursor()
        cur.execute("""
            SELECT i.id,
                   'INC-' || LPAD(i.id::text, 4, '0') AS incident_id,
                   i.antenne_id,
                   a.nom AS antenne,
                   a.zone,
                   i.titre,
                   COALESCE(i.type_anomalie, i.titre) AS type_anomalie,
                   i.description,
                   i.statut,
                   i.criticite,
                   i.source_detection,
                   i.metriques,
                   i.duree_minutes,
                   (i.date_creation AT TIME ZONE 'Africa/Tunis')::text AS date_creation,
                   (i.date_resolution AT TIME ZONE 'Africa/Tunis')::text AS date_resolution
            FROM incidents i
            JOIN antennes a ON i.antenne_id = a.id
            ORDER BY i.date_creation DESC
        """)
        data = rows_to_dicts(cur)
        cur.close()
        conn.close()
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@incidents_bp.route("/incidents/<int:incident_id>", methods=["GET"])
@token_required
def incident_details(incident_id):
    try:
        conn = connecter_base_de_donnees()
        cur = conn.cursor()
        cur.execute("""
            SELECT i.id,
                   'INC-' || LPAD(i.id::text, 4, '0') AS incident_id,
                   i.antenne_id,
                   a.nom AS antenne,
                   a.zone,
                   i.titre,
                   COALESCE(i.type_anomalie, i.titre) AS type_anomalie,
                   i.description,
                   i.statut,
                   i.criticite,
                   i.source_detection,
                   i.metriques,
                   i.duree_minutes,
                   (i.date_creation AT TIME ZONE 'Africa/Tunis')::text AS date_creation,
                   (i.date_resolution AT TIME ZONE 'Africa/Tunis')::text AS date_resolution
            FROM incidents i
            JOIN antennes a ON i.antenne_id = a.id
            WHERE i.id = %s
        """, (incident_id,))
        row = cur.fetchone()
        if not row:
            cur.close()
            conn.close()
            return jsonify({"error": "Incident introuvable"}), 404
        cols = [d[0] for d in cur.description]
        cur.close()
        conn.close()
        return jsonify(dict(zip(cols, row)))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@incidents_bp.route("/incidents/<int:incident_id>/resolve", methods=["POST", "PUT"])
@token_required
def resolve_incident(incident_id):
    try:
        conn = connecter_base_de_donnees()
        cur = conn.cursor()
        cur.execute("""
            UPDATE incidents
            SET statut = 'resolu', date_resolution = NOW()
            WHERE id = %s
        """, (incident_id,))
        conn.commit()
        updated = cur.rowcount
        cur.close()
        conn.close()
        if updated == 0:
            return jsonify({"error": "Incident introuvable"}), 404
            
        # Relancer la prédiction IA pour mettre à jour le statut de l'antenne et le dashboard
        run_ai_prediction()
        
        return jsonify({"success": True, "id": incident_id, "statut": "resolu"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@incidents_bp.route("/incidents/<int:incident_id>/commentaires", methods=["GET"])
@token_required
def get_commentaires(incident_id):
    try:
        conn = connecter_base_de_donnees()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, incident_id, utilisateur_nom, role, contenu, statut_validation, etat_resolution, (date_creation AT TIME ZONE 'Africa/Tunis')::text AS date_creation
            FROM commentaires_incidents
            WHERE incident_id = %s
            ORDER BY date_creation DESC
        """, (incident_id,))
        data = rows_to_dicts(cur)
        cur.close()
        conn.close()
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@incidents_bp.route("/incidents/<int:incident_id>/commentaires", methods=["POST"])
@role_required('administrateur', 'ingenieur_reseau', 'technicien_terrain')
def post_commentaire(incident_id):
    data = request.get_json()
    contenu = data.get("contenu")
    if not contenu:
        return jsonify({"error": "Commentaire vide"}), 400
    
    utilisateur_nom = g.current_user["username"]
    role = g.current_user["role"]
    utilisateur_id = g.current_user.get("id") or g.current_user.get("user_id") # Try both id and user_id depending on JWT payload
        
    statut_validation = "validé" if role == "administrateur" else "en attente"

    etat_resolution = data.get("etat_resolution", "en_cours")
    
    try:
        conn = connecter_base_de_donnees()
        cur = conn.cursor()
        
        # Verify incident exists
        cur.execute("SELECT id FROM incidents WHERE id = %s", (incident_id,))
        if not cur.fetchone():
            cur.close()
            conn.close()
            return jsonify({"error": "Incident introuvable"}), 404

        cur.execute("""
            INSERT INTO commentaires_incidents (incident_id, utilisateur_id, utilisateur_nom, role, contenu, statut_validation, etat_resolution)
            VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id
        """, (incident_id, utilisateur_id, utilisateur_nom, role, contenu, statut_validation, etat_resolution))
        conn.commit()
        new_id = cur.fetchone()[0]
        
        # Si le technicien marque comme réglé dès la création du commentaire
        if etat_resolution in ['réglé', 'resolu']:
            cur.execute("UPDATE incidents SET statut = 'resolu', date_resolution = NOW() WHERE id = %s", (incident_id,))
            conn.commit()
            run_ai_prediction()
            
        cur.close()
        conn.close()
        return jsonify({"success": True, "id": new_id, "statut_validation": statut_validation})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@incidents_bp.route("/admin/commentaires", methods=["GET"])
@token_required
def get_all_commentaires_en_attente():
    if g.current_user["role"] != "administrateur":
        return jsonify({"error": "Non autorisé"}), 403
    try:
        conn = connecter_base_de_donnees()
        cur = conn.cursor()
        cur.execute("""
            SELECT c.id, c.incident_id, c.utilisateur_nom, c.role, c.contenu, c.statut_validation, c.etat_resolution, (c.date_creation AT TIME ZONE 'Africa/Tunis')::text AS date_creation,
                   i.titre AS incident_titre
            FROM commentaires_incidents c
            JOIN incidents i ON c.incident_id = i.id
            WHERE c.statut_validation = 'en attente'
            ORDER BY c.date_creation DESC
        """)
        data = rows_to_dicts(cur)
        cur.close()
        conn.close()
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@incidents_bp.route("/commentaires/<int:comment_id>/resolution", methods=["PUT"])
@token_required
def changer_etat_resolution(comment_id):
    data = request.get_json()
    nouvel_etat = data.get("etat_resolution")
    if not nouvel_etat:
        return jsonify({"error": "État manquant"}), 400
        
    try:
        conn = connecter_base_de_donnees()
        cur = conn.cursor()
        cur.execute("""
            UPDATE commentaires_incidents
            SET etat_resolution = %s
            WHERE id = %s RETURNING incident_id
        """, (nouvel_etat, comment_id))
        
        row = cur.fetchone()
        if row and nouvel_etat in ['réglé', 'resolu']:
            # Mettre à jour l'incident lui-même si réglé
            incident_id = row[0]
            cur.execute("UPDATE incidents SET statut = 'resolu', date_resolution = NOW() WHERE id = %s", (incident_id,))
            conn.commit()
            run_ai_prediction()
        else:
            conn.commit()
            
        cur.close()
        conn.close()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@incidents_bp.route("/commentaires/<int:comment_id>/valider", methods=["PUT"])
@token_required
def valider_commentaire(comment_id):
    if g.current_user["role"] != "administrateur":
        return jsonify({"error": "Non autorisé"}), 403
    try:
        conn = connecter_base_de_donnees()
        cur = conn.cursor()
        cur.execute("""
            UPDATE commentaires_incidents
            SET statut_validation = 'validé'
            WHERE id = %s
        """, (comment_id,))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@incidents_bp.route("/commentaires/<int:comment_id>", methods=["DELETE"])
@token_required
def supprimer_commentaire(comment_id):
    if g.current_user["role"] != "administrateur":
        return jsonify({"error": "Non autorisé"}), 403
    try:
        conn = connecter_base_de_donnees()
        cur = conn.cursor()
        cur.execute("DELETE FROM commentaires_incidents WHERE id = %s", (comment_id,))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@incidents_bp.route("/alerts", methods=["GET"])
@token_required
def list_alerts():
    try:
        conn = connecter_base_de_donnees()
        df = pd.read_sql("""
            SELECT id, nom, zone, type, temperature, cpu, ram, signal, debit,
                   latence, packet_loss, disponibilite, statut, date_mesure::text
            FROM antennes_statut
            WHERE statut IN ('alerte', 'critique')
            ORDER BY CASE statut WHEN 'critique' THEN 0 ELSE 1 END, date_mesure DESC
            LIMIT 12
        """, conn)
        conn.close()
        return jsonify(df.to_dict(orient="records"))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@incidents_bp.route("/moderation/activity", methods=["GET"])
@token_required
def get_moderation_activity():
    """
    [PFE] Historique des activités pour le dashboard Modération.
    Remplace les fausses données par les vrais incidents de la base.
    """
    try:
        conn = connecter_base_de_donnees()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, 
                   to_char(date_creation AT TIME ZONE 'Africa/Tunis', 'HH24:MI') as time, 
                   titre as text, 
                   criticite as type, 
                   'Antenne ' || antenne_id as antenne 
            FROM incidents 
            ORDER BY date_creation DESC LIMIT 10
        """)
        data = rows_to_dicts(cur)
        cur.close()
        conn.close()
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@incidents_bp.route("/moderation/users", methods=["GET"])
@token_required
def get_moderation_users():
    """
    [PFE] Liste des utilisateurs pour le panel Modération.
    """
    try:
        conn = connecter_base_de_donnees()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, 
                   username as nom, 
                   role, 
                   status as statut, 
                   0 as actions 
            FROM users 
            ORDER BY id ASC LIMIT 20
        """)
        data = rows_to_dicts(cur)
        cur.close()
        conn.close()
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@incidents_bp.route("/moderation/action", methods=["POST"])
@token_required
def moderation_action():
    data = request.json
    action = data.get("action")
    return jsonify({"success": True, "message": f"Action '{action}' traitée avec succès dans le système."})

