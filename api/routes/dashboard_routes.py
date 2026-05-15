"""
routes/dashboard_routes.py — Endpoints d'administration et de gestion des utilisateurs
Gère le CRUD utilisateurs et les paramètres système (Admin uniquement).
"""
import time
from datetime import datetime
from flask import Blueprint, request, jsonify, g
from werkzeug.security import generate_password_hash

from database.connection import connecter_base_de_donnees, rows_to_dicts
from utils.globals import ADMIN_LOGS, SYSTEM_SETTINGS
from auth.decorators import token_required


admin_bp = Blueprint('admin_bp', __name__)


# ════════════════════════════════════════════════════════════════
#  GESTION DES UTILISATEURS (Admin uniquement)
# ════════════════════════════════════════════════════════════════

def _check_admin():
    """Vérifie que l'utilisateur courant est administrateur."""
    if g.current_user.get("role") != "administrateur":
        return jsonify({"error": "Accès réservé aux administrateurs"}), 403
    return None


def _map_role(role):
    """Convertit les noms de rôles frontend vers les noms DB."""
    mapping = {
        "ingenieur":  "ingenieur_reseau",
        "technicien": "technicien_terrain",
    }
    return mapping.get(role, role)


@admin_bp.route("/admin/users", methods=["GET"])
@token_required
def get_users():
    """Retourne la liste complète des utilisateurs."""
    err = _check_admin()
    if err: return err
    try:
        conn = connecter_base_de_donnees()
        cur  = conn.cursor()
        cur.execute("""
            SELECT
                id,
                username,
                fullname      AS nom,
                email,
                role,
                status        AS statut,
                department    AS departement,
                phone         AS telephone,
                last_login::text AS derniere_connexion
            FROM users
            ORDER BY id ASC
        """)
        users = rows_to_dicts(cur)
        cur.close(); conn.close()
        return jsonify(users)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@admin_bp.route("/admin/users", methods=["POST"])
@token_required
def create_user():
    """Crée un nouvel utilisateur (Admin uniquement)."""
    err = _check_admin()
    if err: return err

    data        = request.get_json() or {}
    username    = data.get("username", "").strip()
    nom         = data.get("nom", "")
    email       = data.get("email", "")
    role        = _map_role(data.get("role", "observateur"))
    statut      = data.get("statut", "Actif")
    password    = data.get("password", username + "123")
    departement = data.get("departement", "")
    telephone   = data.get("telephone", "")

    if not username:
        return jsonify({"error": "Le nom d'utilisateur est requis"}), 400

    password_hash = generate_password_hash(password)

    try:
        conn = connecter_base_de_donnees()
        cur  = conn.cursor()
        cur.execute("""
            INSERT INTO users
                (username, fullname, email, password_hash, role, status, department, phone)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (username, nom, email, password_hash, role, statut, departement, telephone))
        conn.commit()
        new_id = cur.fetchone()[0]
        cur.close(); conn.close()

        ADMIN_LOGS.insert(0, {
            "id": int(time.time()),
            "heure": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "utilisateur": g.current_user["username"],
            "action": f"Création utilisateur '{username}'",
            "statut": "Succès"
        })
        return jsonify({"success": True, "id": new_id}), 201
    except Exception as e:
        print(f"[ERREUR] POST /admin/users : {e}")
        return jsonify({"error": str(e)}), 500


@admin_bp.route("/admin/users/<int:user_id>", methods=["PUT"])
@token_required
def update_user(user_id):
    """Met à jour les informations d'un utilisateur."""
    err = _check_admin()
    if err: return err

    data        = request.get_json() or {}
    nom         = data.get("nom")
    email       = data.get("email")
    role        = _map_role(data.get("role")) if data.get("role") else None
    statut      = data.get("statut")
    password    = data.get("password")
    departement = data.get("departement")
    telephone   = data.get("telephone")

    try:
        conn = connecter_base_de_donnees()
        cur  = conn.cursor()

        # Cas 1 : Changement de statut uniquement (ex: activer/désactiver)
        if role is None and statut is not None and not nom:
            cur.execute("UPDATE users SET status=%s WHERE id=%s", (statut, user_id))
        # Cas 2 : Mise à jour complète avec nouveau mot de passe
        elif password:
            pwd_hash = generate_password_hash(password)
            cur.execute("""
                UPDATE users
                SET fullname=%s, email=%s, role=%s, status=%s,
                    department=%s, phone=%s, password_hash=%s
                WHERE id=%s
            """, (nom, email, role, statut, departement, telephone, pwd_hash, user_id))
        # Cas 3 : Mise à jour complète sans mot de passe
        else:
            cur.execute("""
                UPDATE users
                SET fullname=%s, email=%s, role=%s, status=%s, department=%s, phone=%s
                WHERE id=%s
            """, (nom, email, role, statut, departement, telephone, user_id))

        conn.commit()
        cur.close(); conn.close()
        return jsonify({"success": True})
    except Exception as e:
        print(f"[ERREUR] PUT /admin/users/{user_id} : {e}")
        return jsonify({"error": str(e)}), 500


@admin_bp.route("/admin/users/<int:user_id>", methods=["DELETE"])
@token_required
def delete_user(user_id):
    """Supprime un utilisateur (Admin uniquement)."""
    err = _check_admin()
    if err: return err
    try:
        conn = connecter_base_de_donnees()
        cur  = conn.cursor()
        cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
        conn.commit()
        cur.close(); conn.close()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ════════════════════════════════════════════════════════════════
#  PARAMÈTRES SYSTÈME
# ════════════════════════════════════════════════════════════════

@admin_bp.route("/admin/settings", methods=["GET"])
@token_required
def get_settings():
    """Retourne les paramètres système actuels."""
    err = _check_admin()
    if err: return err
    return jsonify(SYSTEM_SETTINGS)


@admin_bp.route("/admin/settings", methods=["POST"])
@token_required
def update_settings():
    """Met à jour les paramètres système."""
    err = _check_admin()
    if err: return err
    data = request.get_json() or {}
    for k, v in data.items():
        SYSTEM_SETTINGS[k] = v
    return jsonify({"success": True})


# ════════════════════════════════════════════════════════════════
#  LOGS D'ADMINISTRATION
# ════════════════════════════════════════════════════════════════

@admin_bp.route("/admin/logs", methods=["GET"])
@token_required
def get_admin_logs():
    """Retourne les logs d'activité administrateur (en mémoire)."""
    err = _check_admin()
    if err: return err
    return jsonify(ADMIN_LOGS[:50])
