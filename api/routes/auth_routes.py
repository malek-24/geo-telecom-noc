import os, time, json, random, io
import jwt
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


auth_bp = Blueprint('auth_bp', __name__)

def init_db_users():
    """
    Initialise la table des utilisateurs avec les 4 rôles RBAC,
    et crée la table de chat interne.
    """
    try:
        conn = connecter_base_de_donnees()
        cur = conn.cursor()

        # Table utilisateurs
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                fullname VARCHAR(100),
                email VARCHAR(100),
                password_hash VARCHAR(255),
                role VARCHAR(50),
                department VARCHAR(100),
                phone VARCHAR(20),
                status VARCHAR(20) DEFAULT 'Actif',
                last_login TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # Table messages chat interne
        cur.execute("""
            CREATE TABLE IF NOT EXISTS messages_chat (
                id SERIAL PRIMARY KEY,
                auteur_id INTEGER REFERENCES users(id),
                auteur_nom VARCHAR(100),
                auteur_role VARCHAR(50),
                contenu TEXT NOT NULL,
                date_envoi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # Seed utilisateurs de démo avec les 4 rôles RBAC
        cur.execute("SELECT COUNT(*) FROM users")
        if cur.fetchone()[0] == 0:
            seed_users = [
                ('admin',      'Malek Admin',          'admin@tunisietelecom.tn',    'admin123',   'administrateur',    'Direction NOC',      '73000000'),
                ('ingenieur',  'Hatem Ingénieur',      'ing@tunisietelecom.tn',      'ing123',     'ingenieur_reseau',  'Infrastructure',     '73000001'),
                ('technicien', 'Rami Technicien',      'tech@tunisietelecom.tn',     'tech123',    'technicien_terrain','Interventions',      '73000003'),
            ]
            for u in seed_users:
                cur.execute("""
                    INSERT INTO users (username, fullname, email, password_hash, role, department, phone, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, 'Actif')
                """, (u[0], u[1], u[2], generate_password_hash(u[3]), u[4], u[5], u[6]))

        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print("Erreur initialisation DB:", e)

init_db_users()


@auth_bp.route("/health", methods=["GET"])
def health():
    """Healthcheck endpoint pour Docker."""
    return jsonify({"status": "ok"}), 200

@auth_bp.route("/auth/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    username = data.get("username")
    password = data.get("password")
    
    conn = connecter_base_de_donnees()
    cur = conn.cursor()
    cur.execute("SELECT id, username, fullname, role, status, password_hash FROM users WHERE username = %s OR email = %s", (username, username))
    user = cur.fetchone()
    
    if user and check_password_hash(user[5], password):
        if user[4] == "Inactif" or user[4] == "Désactivé":
            cur.close(); conn.close()
            return jsonify({"error": "Compte désactivé"}), 403
            
        cur.execute("UPDATE users SET last_login = NOW() WHERE id = %s", (user[0],))
        conn.commit()
        cur.close(); conn.close()
        
        payload = {
            "id": user[0],
            "username": user[1],
            "role": user[3],
            "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
        }
        token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
        ADMIN_LOGS.insert(0, {"id": int(time.time()), "heure": datetime.now().strftime("%Y-%m-%d %H:%M"), "utilisateur": user[2], "action": "Connexion réussie", "statut": "Succès"})
        
        return jsonify({
            "token": token,
            "username": user[1],
            "role": user[3]
        })
    
    cur.close(); conn.close()
    return jsonify({"error": "Identifiants invalides"}), 401

@auth_bp.route("/auth/me", methods=["GET"])
@token_required
def me():
    return jsonify(g.current_user)

