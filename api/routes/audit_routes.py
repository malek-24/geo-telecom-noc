"""
routes/audit_routes.py — Journal d'audit (consultation + export)
"""
import io
from flask import Blueprint, jsonify, request, Response

from database.connection import connecter_base_de_donnees, rows_to_dicts
from auth.decorators import admin_required

audit_bp = Blueprint("audit_bp", __name__)


@audit_bp.route("/audit", methods=["GET"])
@admin_required
def list_audit_logs():
    """Liste filtrable des entrées d'audit."""
    utilisateur = request.args.get("utilisateur", "").strip()
    type_action = request.args.get("type_action", "").strip()
    type_objet = request.args.get("type_objet", "").strip()
    ressource = request.args.get("ressource", "").strip()
    date_de = request.args.get("date_de", "").strip()
    date_a = request.args.get("date_a", "").strip()
    limit = min(request.args.get("limit", 500, type=int), 2000)

    clauses = ["1=1"]
    params = []

    if utilisateur:
        clauses.append("utilisateur ILIKE %s")
        params.append(f"%{utilisateur}%")
    if type_action:
        clauses.append("action ILIKE %s")
        params.append(f"%{type_action}%")
    if type_objet:
        clauses.append("type_objet ILIKE %s")
        params.append(f"%{type_objet}%")
    if ressource:
        clauses.append("cible ILIKE %s")
        params.append(f"%{ressource}%")
    if date_de:
        clauses.append("date_action::date >= %s::date")
        params.append(date_de)
    if date_a:
        clauses.append("date_action::date <= %s::date")
        params.append(date_a)

    where_sql = " AND ".join(clauses)
    params.append(limit)

    try:
        conn = connecter_base_de_donnees()
        cur = conn.cursor()
        cur.execute(f"""
            SELECT
                id,
                utilisateur,
                action,
                cible,
                COALESCE(type_objet, '') AS type_objet,
                COALESCE(valeur_avant, '') AS valeur_avant,
                COALESCE(valeur_apres, '') AS valeur_apres,
                COALESCE(adresse_ip, '') AS adresse_ip,
                to_char((date_action AT TIME ZONE 'UTC') AT TIME ZONE 'Africa/Tunis',
                    'YYYY-MM-DD"T"HH24:MI:SS') || '+01:00' AS date
            FROM audit_logs
            WHERE {where_sql}
            ORDER BY date_action DESC
            LIMIT %s
        """, params)
        data = rows_to_dicts(cur)
        cur.close()
        conn.close()
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@audit_bp.route("/audit/export", methods=["GET"])
@admin_required
def export_audit_csv():
    """Export CSV du journal filtré."""
    utilisateur = request.args.get("utilisateur", "").strip()
    type_action = request.args.get("type_action", "").strip()
    type_objet = request.args.get("type_objet", "").strip()
    ressource = request.args.get("ressource", "").strip()
    date_de = request.args.get("date_de", "").strip()
    date_a = request.args.get("date_a", "").strip()

    clauses = ["1=1"]
    params = []

    if utilisateur:
        clauses.append("utilisateur ILIKE %s")
        params.append(f"%{utilisateur}%")
    if type_action:
        clauses.append("action ILIKE %s")
        params.append(f"%{type_action}%")
    if type_objet:
        clauses.append("type_objet ILIKE %s")
        params.append(f"%{type_objet}%")
    if ressource:
        clauses.append("cible ILIKE %s")
        params.append(f"%{ressource}%")
    if date_de:
        clauses.append("date_action::date >= %s::date")
        params.append(date_de)
    if date_a:
        clauses.append("date_action::date <= %s::date")
        params.append(date_a)

    where_sql = " AND ".join(clauses)

    try:
        conn = connecter_base_de_donnees()
        cur = conn.cursor()
        cur.execute(f"""
            SELECT
                to_char((date_action AT TIME ZONE 'UTC') AT TIME ZONE 'Africa/Tunis',
                    'YYYY-MM-DD HH24:MI:SS') AS date_heure,
                utilisateur,
                action,
                type_objet,
                cible,
                valeur_avant,
                valeur_apres,
                adresse_ip
            FROM audit_logs
            WHERE {where_sql}
            ORDER BY date_action DESC
            LIMIT 5000
        """, params)
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description]
        cur.close()
        conn.close()

        buffer = io.StringIO()
        buffer.write(",".join(cols) + "\n")
        for row in rows:
            line = []
            for cell in row:
                text = str(cell or "").replace('"', '""')
                line.append(f'"{text}"')
            buffer.write(",".join(line) + "\n")

        return Response(
            buffer.getvalue(),
            mimetype="text/csv; charset=utf-8",
            headers={"Content-Disposition": "attachment; filename=journal_audit.csv"},
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500
