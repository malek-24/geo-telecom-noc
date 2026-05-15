"""
routes/auth_routes.py — Authentification JWT et initialisation des utilisateurs
Gère la connexion, la vérification de session et le seed des utilisateurs de démo.
"""
import time
import jwt
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, g
from werkzeug.security import generate_password_hash, check_password_hash

from database.connection import connecter_base_de_donnees, rows_to_dicts
from utils.globals import JWT_SECRET, JWT_EXPIRATION_HOURS, ADMIN_LOGS
from auth.decorators import token_required


auth_bp = Blueprint('auth_bp', __name__)


def init_db_users():
    """
    Initialise les tables utilisateurs et messages_chat si absentes,
    et insère les utilisateurs de démo avec les 3 rôles RBAC.
    """
    try:
        conn = connecter_base_de_donnees()
        cur  = conn.cursor()

        # ── Table utilisateurs ────────────────────────────────────────
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id            SERIAL PRIMARY KEY,
                username      VARCHAR(50)  UNIQUE NOT NULL,
                fullname      VARCHAR(100),
                email         VARCHAR(100),
                password_hash VARCHAR(255),
                role          VARCHAR(50),
                department    VARCHAR(100),
                phone         VARCHAR(20),
                status        VARCHAR(20)  DEFAULT 'Actif',
                last_login    TIMESTAMP,
                created_at    TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # ── Table messages chat interne ───────────────────────────────
        cur.execute("""
            CREATE TABLE IF NOT EXISTS messages_chat (
                id          SERIAL PRIMARY KEY,
                auteur_id   INTEGER REFERENCES users(id),
                auteur_nom  VARCHAR(100),
                auteur_role VARCHAR(50),
                contenu     TEXT NOT NULL,
                date_envoi  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # ── Seed utilisateurs de démo ─────────────────────────────────
        cur.execute("SELECT COUNT(*) FROM users")
        if cur.fetchone()[0] == 0:
            seed_users = [
                ('admin',      'Malek Admin',     'admin@tunisietelecom.tn',  'admin123',  'administrateur',    'Direction NOC',   '73000000'),
                ('ingenieur',  'Hatem Ingénieur', 'ing@tunisietelecom.tn',    'ing123',    'ingenieur_reseau',  'Infrastructure',  '73000001'),
                ('technicien', 'Rami Technicien', 'tech@tunisietelecom.tn',   'tech123',   'technicien_terrain','Interventions',   '73000003'),
            ]
            for u in seed_users:
                cur.execute("""
                    INSERT INTO users (username, fullname, email, password_hash, role, department, phone, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, 'Actif')
                """, (u[0], u[1], u[2], generate_password_hash(u[3]), u[4], u[5], u[6]))

        conn.commit()
        cur.close()
        conn.close()
        print("[INIT] Utilisateurs de démo prêts.")
    except Exception as e:
        print(f"[ERREUR INIT USERS] {e}")


# Initialisation au démarrage du blueprint
init_db_users()


# ── Connexion ─────────────────────────────────────────────────────
@auth_bp.route("/auth/login", methods=["POST"])
def login():
    """
    Authentifie un utilisateur par username/email + mot de passe.
    Retourne un JWT valable JWT_EXPIRATION_HOURS heures.
    """
    data     = request.get_json() or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username or not password:
        return jsonify({"error": "Identifiants manquants"}), 400

    try:
        conn = connecter_base_de_donnees()
        cur  = conn.cursor()
        cur.execute(
            "SELECT id, username, fullname, role, status, password_hash "
            "FROM users WHERE username = %s OR email = %s",
            (username, username)
        )
        user = cur.fetchone()

        if not user or not check_password_hash(user[5], password):
            cur.close(); conn.close()
            return jsonify({"error": "Identifiants invalides"}), 401

        if user[4] in ("Inactif", "Désactivé"):
            cur.close(); conn.close()
            return jsonify({"error": "Compte désactivé. Contactez l'administrateur."}), 403

        # Mise à jour last_login
        cur.execute("UPDATE users SET last_login = NOW() WHERE id = %s", (user[0],))
        conn.commit()
        cur.close(); conn.close()

        # Génération du token JWT
        payload = {
            "id":       user[0],
            "username": user[1],
            "role":     user[3],
            "exp":      datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
        }
        token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")

        # Log admin
        ADMIN_LOGS.insert(0, {
            "id":          int(time.time()),
            "heure":       datetime.now().strftime("%Y-%m-%d %H:%M"),
            "utilisateur": user[2],
            "action":      "Connexion réussie",
            "statut":      "Succès"
        })

        return jsonify({"token": token, "username": user[1], "role": user[3]})

    except Exception as e:
        print(f"[ERREUR LOGIN] {e}")
        return jsonify({"error": "Erreur serveur"}), 500


# ── Vérification de session ───────────────────────────────────────
@auth_bp.route("/auth/me", methods=["GET"])
@token_required
def me():
    """Retourne les informations de l'utilisateur courant (depuis le JWT)."""
    return jsonify(g.current_user)
