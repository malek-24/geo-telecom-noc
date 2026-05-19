"""
routes/chat_routes.py — Chat interne NOC avec messagerie privée
Permet la communication directe entre utilisateurs (discussions privées).
"""
from flask import Blueprint, request, jsonify, g
from database.connection import connecter_base_de_donnees, rows_to_dicts
from auth.decorators import token_required

chat_bp = Blueprint('chat_bp', __name__)


def _init_chat_tables(conn):
    """Crée les tables de chat si elles n'existent pas."""
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS messages_chat (
            id          SERIAL PRIMARY KEY,
            auteur_id   INTEGER REFERENCES users(id) ON DELETE SET NULL,
            auteur_nom  VARCHAR(100),
            auteur_role VARCHAR(50),
            destinataire_id   INTEGER REFERENCES users(id) ON DELETE SET NULL,
            destinataire_nom  VARCHAR(100),
            contenu     TEXT NOT NULL,
            is_private  BOOLEAN DEFAULT FALSE,
            date_envoi  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    cur.close()


# ── Canal public ──────────────────────────────────────────────

@chat_bp.route("/chat/messages", methods=["GET"])
@token_required
def get_messages_publics():
    """Retourne les 50 derniers messages publics."""
    try:
        conn = connecter_base_de_donnees()
        _init_chat_tables(conn)
        cur = conn.cursor()
        cur.execute("""
            SELECT id, auteur_id, auteur_nom, auteur_role,
                   contenu, date_envoi
            FROM messages_chat
            WHERE is_private = FALSE
            ORDER BY date_envoi DESC
            LIMIT 50
        """)
        rows = rows_to_dicts(cur)
        cur.close(); conn.close()
        return jsonify(list(reversed(rows)))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@chat_bp.route("/chat/messages/new", methods=["GET"])
@token_required
def get_new_messages_publics():
    """Polling — nouveaux messages publics depuis un ID donné."""
    since_id = request.args.get("since_id", 0, type=int)
    try:
        conn = connecter_base_de_donnees()
        _init_chat_tables(conn)
        cur = conn.cursor()
        cur.execute("""
            SELECT id, auteur_id, auteur_nom, auteur_role, contenu, date_envoi
            FROM messages_chat
            WHERE is_private = FALSE AND id > %s
            ORDER BY date_envoi ASC
            LIMIT 30
        """, (since_id,))
        rows = rows_to_dicts(cur)
        cur.close(); conn.close()
        return jsonify(rows)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@chat_bp.route("/chat/messages", methods=["POST"])
@token_required
def envoyer_message_public():
    """Envoie un message dans le canal public."""
    data    = request.get_json() or {}
    contenu = (data.get("contenu") or "").strip()
    if not contenu:
        return jsonify({"error": "Message vide"}), 400
    if len(contenu) > 500:
        return jsonify({"error": "Message trop long (500 caractères max)"}), 400

    user = g.current_user
    try:
        conn = connecter_base_de_donnees()
        _init_chat_tables(conn)
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO messages_chat (auteur_id, auteur_nom, auteur_role, contenu, is_private)
            VALUES (%s, %s, %s, %s, FALSE)
            RETURNING id, auteur_nom, auteur_role, contenu, date_envoi
        """, (user["id"], user["username"], user["role"], contenu))
        row = cur.fetchone()
        conn.commit(); cur.close(); conn.close()
        return jsonify({
            "id":         row[0],
            "auteur_nom": row[1],
            "auteur_role": row[2],
            "contenu":    row[3],
            "date_envoi": row[4].isoformat() if row[4] else None,
        }), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── Messagerie privée ─────────────────────────────────────────

@chat_bp.route("/chat/users", methods=["GET"])
@token_required
def get_utilisateurs_chat():
    """Liste tous les utilisateurs actifs pour la messagerie privée."""
    try:
        conn = connecter_base_de_donnees()
        cur  = conn.cursor()
        cur.execute("""
            SELECT id, username, fullname, role, status
            FROM users
            WHERE status = 'Actif'
            ORDER BY fullname
        """)
        rows = rows_to_dicts(cur)
        cur.close(); conn.close()

        # Exclure l'utilisateur courant
        me = g.current_user["id"]
        rows = [r for r in rows if r["id"] != me]
        return jsonify(rows)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@chat_bp.route("/chat/private/<int:dest_id>", methods=["GET"])
@token_required
def get_messages_prives(dest_id):
    """Retourne la conversation privée entre l'utilisateur courant et dest_id."""
    me = g.current_user["id"]
    try:
        conn = connecter_base_de_donnees()
        _init_chat_tables(conn)
        cur = conn.cursor()
        cur.execute("""
            SELECT id, auteur_id, auteur_nom, auteur_role,
                   destinataire_id, destinataire_nom,
                   contenu, date_envoi
            FROM messages_chat
            WHERE is_private = TRUE
              AND (
                    (auteur_id = %s AND destinataire_id = %s)
                 OR (auteur_id = %s AND destinataire_id = %s)
              )
            ORDER BY date_envoi ASC
            LIMIT 100
        """, (me, dest_id, dest_id, me))
        rows = rows_to_dicts(cur)
        cur.close(); conn.close()
        return jsonify(rows)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@chat_bp.route("/chat/private/<int:dest_id>/new", methods=["GET"])
@token_required
def poll_messages_prives(dest_id):
    """Polling — nouveaux messages privés depuis un ID donné."""
    me       = g.current_user["id"]
    since_id = request.args.get("since_id", 0, type=int)
    try:
        conn = connecter_base_de_donnees()
        _init_chat_tables(conn)
        cur = conn.cursor()
        cur.execute("""
            SELECT id, auteur_id, auteur_nom, auteur_role,
                   destinataire_id, destinataire_nom,
                   contenu, date_envoi
            FROM messages_chat
            WHERE is_private = TRUE AND id > %s
              AND (
                    (auteur_id = %s AND destinataire_id = %s)
                 OR (auteur_id = %s AND destinataire_id = %s)
              )
            ORDER BY date_envoi ASC
            LIMIT 30
        """, (since_id, me, dest_id, dest_id, me))
        rows = rows_to_dicts(cur)
        cur.close(); conn.close()
        return jsonify(rows)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@chat_bp.route("/chat/private/<int:dest_id>", methods=["POST"])
@token_required
def envoyer_message_prive(dest_id):
    """Envoie un message privé à un utilisateur spécifique."""
    data    = request.get_json() or {}
    contenu = (data.get("contenu") or "").strip()
    if not contenu:
        return jsonify({"error": "Message vide"}), 400
    if len(contenu) > 500:
        return jsonify({"error": "Message trop long (500 caractères max)"}), 400

    user = g.current_user
    try:
        conn = connecter_base_de_donnees()
        _init_chat_tables(conn)
        cur = conn.cursor()

        # Récupère le nom du destinataire
        cur.execute("SELECT username, fullname FROM users WHERE id = %s", (dest_id,))
        dest = cur.fetchone()
        if not dest:
            cur.close(); conn.close()
            return jsonify({"error": "Destinataire introuvable"}), 404

        dest_nom = dest[1] or dest[0]

        cur.execute("""
            INSERT INTO messages_chat
                (auteur_id, auteur_nom, auteur_role,
                 destinataire_id, destinataire_nom,
                 contenu, is_private)
            VALUES (%s, %s, %s, %s, %s, %s, TRUE)
            RETURNING id, auteur_nom, auteur_role, contenu, date_envoi
        """, (user["id"], user["username"], user["role"],
              dest_id, dest_nom, contenu))
        row = cur.fetchone()
        conn.commit(); cur.close(); conn.close()

        return jsonify({
            "id":               row[0],
            "auteur_nom":       row[1],
            "auteur_role":      row[2],
            "contenu":          row[3],
            "date_envoi":       row[4].isoformat() if row[4] else None,
            "destinataire_id":  dest_id,
            "destinataire_nom": dest_nom,
            "is_private":       True,
        }), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@chat_bp.route("/chat/private/unread", methods=["GET"])
@token_required
def get_unread_counts():
    """Retourne le nombre de messages non lus par expéditeur."""
    me       = g.current_user["id"]
    since_id = request.args.get("since_id", 0, type=int)
    try:
        conn = connecter_base_de_donnees()
        _init_chat_tables(conn)
        cur = conn.cursor()
        cur.execute("""
            SELECT auteur_id, auteur_nom, COUNT(*) as count
            FROM messages_chat
            WHERE is_private = TRUE
              AND destinataire_id = %s
              AND id > %s
            GROUP BY auteur_id, auteur_nom
        """, (me, since_id))
        rows = rows_to_dicts(cur)
        cur.close(); conn.close()
        return jsonify(rows)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
