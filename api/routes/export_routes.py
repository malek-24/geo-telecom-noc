"""
routes/export_routes.py — Export CSV (mesures, incidents, antennes)
"""
import io
import pandas as pd
from flask import Blueprint, Response

from flask import g

from database.connection import connecter_base_de_donnees
from auth.decorators import token_required
from utils.audit import enregistrer_audit

export_bp = Blueprint("export_bp", __name__)


def _csv_response(df: pd.DataFrame, filename: str) -> Response:
    buffer = io.StringIO()
    df.to_csv(buffer, index=False)
    return Response(
        buffer.getvalue(),
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@export_bp.route("/export/mesures", methods=["GET"])
@token_required
def export_mesures():
    try:
        conn = connecter_base_de_donnees()
        df = pd.read_sql("""
            SELECT
                m.id,
                a.nom,
                m.temperature,
                m.cpu,
                m.signal,
                m.latence,
                m.disponibilite,
                m.statut AS etat,
                m.risk_score,
                to_char((m.date_mesure AT TIME ZONE 'UTC') AT TIME ZONE 'Africa/Tunis',
                    'YYYY-MM-DD HH24:MI:SS') AS date_mesure
            FROM mesures m
            JOIN antennes a ON a.id = m.antenne_id
            ORDER BY m.date_mesure DESC
            LIMIT 5000
        """, conn)
        enregistrer_audit(
            conn, g.current_user["username"], "Export CSV",
            cible="export_mesures.csv", type_objet="export",
        )
        conn.close()
        return _csv_response(df, "export_mesures.csv")
    except Exception as e:
        return Response(f"error,{e}", mimetype="text/plain"), 500


@export_bp.route("/export/incidents", methods=["GET"])
@token_required
def export_incidents():
    try:
        conn = connecter_base_de_donnees()
        df = pd.read_sql("""
            SELECT
                i.id,
                a.nom AS antenne,
                i.titre,
                i.statut,
                i.criticite,
                i.source_detection,
                i.risk_score,
                to_char((i.date_creation AT TIME ZONE 'UTC') AT TIME ZONE 'Africa/Tunis',
                    'YYYY-MM-DD HH24:MI:SS') AS date_creation,
                to_char((i.date_resolution AT TIME ZONE 'UTC') AT TIME ZONE 'Africa/Tunis',
                    'YYYY-MM-DD HH24:MI:SS') AS date_resolution
            FROM incidents i
            JOIN antennes a ON a.id = i.antenne_id
            ORDER BY i.date_creation DESC
        """, conn)
        enregistrer_audit(
            conn, g.current_user["username"], "Export CSV",
            cible="export_incidents.csv", type_objet="export",
        )
        conn.close()
        return _csv_response(df, "export_incidents.csv")
    except Exception as e:
        return Response(f"error,{e}", mimetype="text/plain"), 500


@export_bp.route("/export/antennes", methods=["GET"])
@token_required
def export_antennes():
    try:
        conn = connecter_base_de_donnees()
        df = pd.read_sql("""
            SELECT
                s.id,
                s.nom,
                s.zone,
                s.type,
                s.statut AS etat,
                s.risk_score,
                s.temperature,
                s.cpu,
                s.signal,
                s.latence,
                s.disponibilite
            FROM antennes_statut s
            ORDER BY s.id
        """, conn)
        enregistrer_audit(
            conn, g.current_user["username"], "Export CSV",
            cible="export_antennes.csv", type_objet="export",
        )
        conn.close()
        return _csv_response(df, "export_antennes.csv")
    except Exception as e:
        return Response(f"error,{e}", mimetype="text/plain"), 500
