"""
routes/chat_routes.py — Chat interne NOC avec messagerie privée
"""
from flask import Blueprint, request, jsonify, g
from database.connection import connecter_base_de_donnees, rows_to_dicts
from auth.decorators import token_required
from utils.db_extensions import initialiser_tables_extensions
from utils.audit import enregistrer_audit
from utils.datetime_tz import sql_col_tunisia, format_dt_tunisia

chat_bp = Blueprint('chat_bp', __name__)

DATE_COL = sql_col_tunisia("date_envoi")


def _init_chat_tables(conn):
    initialiser_tables_extensions(conn)


def _serialize_message_row(row_dict):
    """Assure date_envoi au format Tunisie si présent en datetime."""
    if row_dict.get("date_envoi") and not isinstance(row_dict["date_envoi"], str):
        row_dict["date_envoi"] = format_dt_tunisia(row_dict["date_envoi"])
    return row_dict


def _rows_tn(cur):
    return [_serialize_message_row(r) for r in rows_to_dicts(cur)]


def _peer_id_for_public():
    return 0


def _marquer_lu(conn, user_id: int, peer_id: int) -> None:
    """Met à jour le dernier message lu pour une conversation."""
    cur = conn.cursor()
    if peer_id == _peer_id_for_public():
        cur.execute("""
            SELECT COALESCE(MAX(id), 0) FROM messages_chat
            WHERE is_private = FALSE
        """)
    else:
        cur.execute("""
            SELECT COALESCE(MAX(id), 0) FROM messages_chat
            WHERE is_private = TRUE
              AND (
                    (auteur_id = %s AND destinataire_id = %s)
                 OR (auteur_id = %s AND destinataire_id = %s)
              )
        """, (user_id, peer_id, peer_id, user_id))
    max_id = cur.fetchone()[0]
    cur.execute("""
        INSERT INTO chat_lectures (user_id, peer_id, last_read_id, updated_at)
        VALUES (%s, %s, %s, NOW())
        ON CONFLICT (user_id, peer_id)
        DO UPDATE SET last_read_id = EXCLUDED.last_read_id, updated_at = NOW()
    """, (user_id, peer_id, max_id))
    cur.close()


# ── Canal public ──────────────────────────────────────────────

@chat_bp.route("/chat/messages", methods=["GET"])
@token_required
def get_messages_publics():
    try:
        conn = connecter_base_de_donnees()
        _init_chat_tables(conn)
        cur = conn.cursor()
        cur.execute(f"""
            SELECT id, auteur_id, auteur_nom, auteur_role,
                   contenu, {DATE_COL} AS date_envoi
            FROM messages_chat
            WHERE is_private = FALSE
            ORDER BY date_envoi DESC
            LIMIT 50
        """)
        rows = _rows_tn(cur)
        _marquer_lu(conn, g.current_user["id"], _peer_id_for_public())
        conn.commit()
        cur.close()
        conn.close()
        return jsonify(list(reversed(rows)))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@chat_bp.route("/chat/messages/new", methods=["GET"])
@token_required
def get_new_messages_publics():
    since_id = request.args.get("since_id", 0, type=int)
    try:
        conn = connecter_base_de_donnees()
        _init_chat_tables(conn)
        cur = conn.cursor()
        cur.execute(f"""
            SELECT id, auteur_id, auteur_nom, auteur_role, contenu,
                   {DATE_COL} AS date_envoi
            FROM messages_chat
            WHERE is_private = FALSE AND id > %s
            ORDER BY date_envoi ASC
            LIMIT 30
        """, (since_id,))
        rows = _rows_tn(cur)
        cur.close()
        conn.close()
        return jsonify(rows)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@chat_bp.route("/chat/messages", methods=["POST"])
@token_required
def envoyer_message_public():
    data = request.get_json() or {}
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
            RETURNING id, auteur_id, auteur_nom, auteur_role, contenu, date_envoi
        """, (user["id"], user["username"], user["role"], contenu))
        row = cur.fetchone()
        enregistrer_audit(
            conn, user["username"], "Envoi message",
            cible="canal public", type_objet="message",
            valeur_apres=contenu[:200],
        )
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({
            "id": row[0],
            "auteur_id": row[1],
            "auteur_nom": row[2],
            "auteur_role": row[3],
            "contenu": row[4],
            "date_envoi": format_dt_tunisia(row[5]),
        }), 201
    except Exception as e:
        print(f"[CHAT] POST public : {e}")
        return jsonify({"error": str(e)}), 500


@chat_bp.route("/chat/messages/read", methods=["POST"])
@token_required
def marquer_public_lu():
    try:
        conn = connecter_base_de_donnees()
        _init_chat_tables(conn)
        _marquer_lu(conn, g.current_user["id"], _peer_id_for_public())
        conn.commit()
        conn.close()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── Messagerie privée ─────────────────────────────────────────

@chat_bp.route("/chat/users", methods=["GET"])
@token_required
def get_utilisateurs_chat():
    try:
        conn = connecter_base_de_donnees()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, username, fullname, role, status
            FROM users
            WHERE status = 'Actif'
            ORDER BY fullname
        """)
        rows = rows_to_dicts(cur)
        cur.close()
        conn.close()
        me = g.current_user["id"]
        return jsonify([r for r in rows if r["id"] != me])
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@chat_bp.route("/chat/private/<int:dest_id>", methods=["GET"])
@token_required
def get_messages_prives(dest_id):
    me = g.current_user["id"]
    try:
        conn = connecter_base_de_donnees()
        _init_chat_tables(conn)
        cur = conn.cursor()
        cur.execute(f"""
            SELECT id, auteur_id, auteur_nom, auteur_role,
                   destinataire_id, destinataire_nom,
                   contenu, {DATE_COL} AS date_envoi
            FROM messages_chat
            WHERE is_private = TRUE
              AND (
                    (auteur_id = %s AND destinataire_id = %s)
                 OR (auteur_id = %s AND destinataire_id = %s)
              )
            ORDER BY date_envoi ASC
            LIMIT 100
        """, (me, dest_id, dest_id, me))
        rows = _rows_tn(cur)
        _marquer_lu(conn, me, dest_id)
        conn.commit()
        cur.close()
        conn.close()
        return jsonify(rows)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@chat_bp.route("/chat/private/<int:dest_id>/new", methods=["GET"])
@token_required
def poll_messages_prives(dest_id):
    me = g.current_user["id"]
    since_id = request.args.get("since_id", 0, type=int)
    try:
        conn = connecter_base_de_donnees()
        _init_chat_tables(conn)
        cur = conn.cursor()
        cur.execute(f"""
            SELECT id, auteur_id, auteur_nom, auteur_role,
                   destinataire_id, destinataire_nom,
                   contenu, {DATE_COL} AS date_envoi
            FROM messages_chat
            WHERE is_private = TRUE AND id > %s
              AND (
                    (auteur_id = %s AND destinataire_id = %s)
                 OR (auteur_id = %s AND destinataire_id = %s)
              )
            ORDER BY date_envoi ASC
            LIMIT 30
        """, (since_id, me, dest_id, dest_id, me))
        rows = _rows_tn(cur)
        cur.close()
        conn.close()
        return jsonify(rows)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@chat_bp.route("/chat/private/<int:dest_id>", methods=["POST"])
@token_required
def envoyer_message_prive(dest_id):
    data = request.get_json() or {}
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
        cur.execute("SELECT username, fullname FROM users WHERE id = %s", (dest_id,))
        dest = cur.fetchone()
        if not dest:
            cur.close()
            conn.close()
            return jsonify({"error": "Destinataire introuvable"}), 404

        dest_nom = dest[1] or dest[0]
        cur.execute("""
            INSERT INTO messages_chat
                (auteur_id, auteur_nom, auteur_role,
                 destinataire_id, destinataire_nom,
                 contenu, is_private)
            VALUES (%s, %s, %s, %s, %s, %s, TRUE)
            RETURNING id, auteur_id, auteur_nom, auteur_role, contenu, date_envoi
        """, (user["id"], user["username"], user["role"], dest_id, dest_nom, contenu))
        row = cur.fetchone()
        enregistrer_audit(
            conn, user["username"], "Envoi message privé",
            cible=dest_nom, type_objet="message",
            valeur_apres=contenu[:200],
        )
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({
            "id": row[0],
            "auteur_id": row[1],
            "auteur_nom": row[2],
            "auteur_role": row[3],
            "contenu": row[4],
            "date_envoi": format_dt_tunisia(row[5]),
            "destinataire_id": dest_id,
            "destinataire_nom": dest_nom,
            "is_private": True,
        }), 201
    except Exception as e:
        print(f"[CHAT] POST privé vers {dest_id} : {e}")
        return jsonify({"error": str(e)}), 500


@chat_bp.route("/chat/private/<int:dest_id>/read", methods=["POST"])
@token_required
def marquer_prive_lu(dest_id):
    try:
        conn = connecter_base_de_donnees()
        _init_chat_tables(conn)
        _marquer_lu(conn, g.current_user["id"], dest_id)
        conn.commit()
        conn.close()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@chat_bp.route("/chat/unread/summary", methods=["GET"])
@token_required
def resume_non_lus():
    """Nombre total de messages non lus (public + privés)."""
    me = g.current_user["id"]
    try:
        conn = connecter_base_de_donnees()
        _init_chat_tables(conn)
        cur = conn.cursor()
        cur.execute("""
            SELECT COUNT(*)::int FROM messages_chat m
            WHERE m.is_private = FALSE
              AND m.auteur_id IS DISTINCT FROM %s
              AND m.id > COALESCE(
                (SELECT last_read_id FROM chat_lectures
                 WHERE user_id = %s AND peer_id = 0), 0)
        """, (me, me))
        public_count = cur.fetchone()[0]
        cur.execute("""
            SELECT COUNT(*)::int FROM messages_chat m
            WHERE m.is_private = TRUE
              AND m.destinataire_id = %s
              AND m.id > COALESCE(
                (SELECT last_read_id FROM chat_lectures cl
                 WHERE cl.user_id = %s AND cl.peer_id = m.auteur_id), 0)
        """, (me, me))
        private_count = cur.fetchone()[0]
        cur.execute("""
            SELECT m.auteur_id, m.auteur_nom, COUNT(*)::int AS count
            FROM messages_chat m
            WHERE m.is_private = TRUE
              AND m.destinataire_id = %s
              AND m.id > COALESCE(
                (SELECT last_read_id FROM chat_lectures cl
                 WHERE cl.user_id = %s AND cl.peer_id = m.auteur_id), 0)
            GROUP BY m.auteur_id, m.auteur_nom
        """, (me, me))
        par_expediteur = rows_to_dicts(cur)
        cur.close()
        conn.close()
        total = public_count + private_count
        return jsonify({
            "total": total,
            "public": public_count,
            "private": private_count,
            "par_expediteur": par_expediteur,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@chat_bp.route("/chat/private/unread", methods=["GET"])
@token_required
def get_unread_counts():
    """Compatibilité : compte par expéditeur."""
    me = g.current_user["id"]
    try:
        conn = connecter_base_de_donnees()
        _init_chat_tables(conn)
        cur = conn.cursor()
        cur.execute("""
            SELECT m.auteur_id, m.auteur_nom, COUNT(*)::int AS count
            FROM messages_chat m
            WHERE m.is_private = TRUE
              AND m.destinataire_id = %s
              AND m.id > COALESCE(
                (SELECT last_read_id FROM chat_lectures cl
                 WHERE cl.user_id = %s AND cl.peer_id = m.auteur_id), 0)
            GROUP BY m.auteur_id, m.auteur_nom
        """, (me, me))
        rows = rows_to_dicts(cur)
        cur.close()
        conn.close()
        return jsonify(rows)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
