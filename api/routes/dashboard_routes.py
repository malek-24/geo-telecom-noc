import os, time, json, random, io
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, g, send_file
import pandas as pd
from werkzeug.security import generate_password_hash, check_password_hash
from database.connection import connecter_base_de_donnees, rows_to_dicts
from utils.globals import JWT_SECRET, JWT_EXPIRATION_HOURS, ADMIN_LOGS, SYSTEM_SETTINGS
from auth.decorators import token_required, admin_required, role_required
from ia.prediction import run_ai_prediction, get_ia_report_anomalies

admin_bp = Blueprint('admin_bp', __name__)

@admin_bp.route("/admin/users", methods=["GET"])
@token_required
def get_users():
    if g.current_user["role"] != "administrateur":
        return jsonify({"error": "Non autorisé"}), 403
    try:
        conn = connecter_base_de_donnees()
        cur = conn.cursor()
        cur.execute("SELECT id, username, fullname as nom, email, role, status as statut, department as departement, phone as telephone, last_login::text as derniere_connexion FROM users ORDER BY id ASC")
        users = rows_to_dicts(cur)
        cur.close()
        conn.close()
        return jsonify(users)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@admin_bp.route("/admin/users", methods=["POST"])
@token_required
def create_user():
    if g.current_user["role"] != "administrateur":
        return jsonify({"error": "Non autorisé"}), 403
    
    data = request.json
    username = data.get("username")
    nom = data.get("nom")
    email = data.get("email")
    role = data.get("role")
    statut = data.get("statut", "Actif")
    password = data.get("password", "")
    departement = data.get("departement", "")
    telephone = data.get("telephone", "")
    
    # Map React role to DB role if necessary
    db_role = role
    if role == "ingenieur": db_role = "ingenieur_reseau"
    elif role == "technicien": db_role = "technicien_terrain"
    
    password_hash = generate_password_hash(password) if password else generate_password_hash(username + "123")
    
    try:
        conn = connecter_base_de_donnees()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO users (username, fullname, email, password_hash, role, status, department, phone)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (username, nom, email, password_hash, db_role, statut, departement, telephone))
        conn.commit()
        new_id = cur.fetchone()[0]
        cur.close()
        conn.close()
        return jsonify({"success": True, "id": new_id})
    except Exception as e:
        print("Erreur création user:", e)
        return jsonify({"error": str(e)}), 500

@admin_bp.route("/admin/users/<int:user_id>", methods=["PUT"])
@token_required
def update_user(user_id):
    if g.current_user["role"] != "administrateur":
        return jsonify({"error": "Non autorisé"}), 403
        
    data = request.json
    nom = data.get("nom")
    email = data.get("email")
    role = data.get("role")
    statut = data.get("statut")
    password = data.get("password")
    departement = data.get("departement")
    telephone = data.get("telephone")
    
    db_role = role
    if role == "ingenieur": db_role = "ingenieur_reseau"
    elif role == "technicien": db_role = "technicien_terrain"

    try:
        conn = connecter_base_de_donnees()
        cur = conn.cursor()
        
        if password:
            pwd_hash = generate_password_hash(password)
            cur.execute("""
                UPDATE users SET fullname=%s, email=%s, role=%s, status=%s, department=%s, phone=%s, password_hash=%s
                WHERE id=%s
            """, (nom, email, db_role, statut, departement, telephone, pwd_hash, user_id))
        else:
            if role is None and statut is not None:
                # Toggle Status case
                cur.execute("UPDATE users SET status=%s WHERE id=%s", (statut, user_id))
            else:
                # Normal update case without password
                cur.execute("""
                    UPDATE users SET fullname=%s, email=%s, role=%s, status=%s, department=%s, phone=%s
                    WHERE id=%s
                """, (nom, email, db_role, statut, departement, telephone, user_id))
                
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"success": True})
    except Exception as e:
        print("Erreur update user:", e)
        return jsonify({"error": str(e)}), 500

@admin_bp.route("/admin/users/<int:user_id>", methods=["DELETE"])
@token_required
def delete_user(user_id):
    if g.current_user["role"] != "administrateur":
        return jsonify({"error": "Non autorisé"}), 403
    try:
        conn = connecter_base_de_donnees()
        cur = conn.cursor()
        cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@admin_bp.route("/admin/settings", methods=["GET"])
@token_required
def get_settings():
    if g.current_user["role"] != "administrateur":
        return jsonify({"error": "Non autorisé"}), 403
    return jsonify(SYSTEM_SETTINGS)

@admin_bp.route("/admin/settings", methods=["POST"])
@token_required
def update_settings():
    if g.current_user["role"] != "administrateur":
        return jsonify({"error": "Non autorisé"}), 403
    data = request.json
    for k, v in data.items():
        SYSTEM_SETTINGS[k] = v
    return jsonify({"success": True})

@admin_bp.route("/stats", methods=["GET"])
@token_required
def dashboard_stats():
    # Helper to avoid duplicate endpoints
    return jsonify({"users": 10, "alerts": 5})
