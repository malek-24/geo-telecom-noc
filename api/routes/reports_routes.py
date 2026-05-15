"""
routes/reports_routes.py — Génération de rapports PDF, Excel et CSV
Expose les endpoints de génération de documents pour le module Rapports.
"""
import io
from datetime import datetime
from flask import Blueprint, request, jsonify, g, send_file
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm

from database.connection import connecter_base_de_donnees, rows_to_dicts
from auth.decorators import token_required
from ia.prediction import get_ia_report_anomalies


reports_bp = Blueprint('reports_bp', __name__)


# ════════════════════════════════════════════════════════════════
#  UTILITAIRES PDF
# ════════════════════════════════════════════════════════════════

def _create_pdf_canvas(title: str):
    """
    Crée un canvas ReportLab avec un en-tête standard.
    Retourne (buffer, canvas, width, height).
    """
    buffer   = io.BytesIO()
    c        = canvas.Canvas(buffer, pagesize=A4)
    w, h     = A4
    c.setFont("Helvetica-Bold", 16)
    c.drawString(2*cm, h - 2*cm, title)
    c.setFont("Helvetica", 10)
    c.drawString(2*cm, h - 2.8*cm, f"Date : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    c.drawString(2*cm, h - 3.2*cm, "Tunisie Telecom — Direction Régionale Mahdia")
    c.line(2*cm, h - 3.5*cm, w - 2*cm, h - 3.5*cm)
    return buffer, c, w, h


# ════════════════════════════════════════════════════════════════
#  LISTE DES RAPPORTS DISPONIBLES
# ════════════════════════════════════════════════════════════════

@reports_bp.route("/reports/history", methods=["GET"])
@token_required
def get_reports_history():
    """
    Retourne la liste dynamique des rapports disponibles
    (basée sur la date du jour).
    """
    today = datetime.now().strftime("%d/%m/%Y")
    return jsonify([
        {
            "id": "REP-DAILY-01", "nom": "Rapport Quotidien NOC",
            "type": "daily", "date": f"{today} 08:00",
            "auteur": "Système", "taille": "2.4 MB", "statut": "Prêt"
        },
        {
            "id": "REP-IA-02", "nom": "Analyse Anomalies IA",
            "type": "ia", "date": f"{today} 10:30",
            "auteur": "IA Auto", "taille": "1.1 MB", "statut": "Prêt"
        },
        {
            "id": "REP-INC-03", "nom": "Rapport des Incidents",
            "type": "incidents", "date": f"{today} 12:00",
            "auteur": "Système", "taille": "0.8 MB", "statut": "Prêt"
        },
    ])


# ════════════════════════════════════════════════════════════════
#  RAPPORT QUOTIDIEN PDF
# ════════════════════════════════════════════════════════════════

@reports_bp.route("/rapport/quotidien", methods=["GET"])
@reports_bp.route("/reports/daily-pdf", methods=["GET"])   # alias
@token_required
def rapport_quotidien():
    """Génère et télécharge le rapport PDF quotidien du réseau."""
    try:
        conn = connecter_base_de_donnees()
        cur  = conn.cursor()

        cur.execute("SELECT COUNT(*) FROM antennes")
        total = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM antennes_statut WHERE statut IN ('alerte', 'critique')")
        alertes = cur.fetchone()[0]

        cur.execute("SELECT AVG(disponibilite), AVG(cpu), AVG(temperature) FROM antennes_statut")
        row = cur.fetchone()
        dispo, avg_cpu, avg_temp = float(row[0] or 100), float(row[1] or 0), float(row[2] or 0)

        cur.execute("""
            SELECT i.titre, i.criticite, i.statut, i.date_creation, a.nom
            FROM incidents i
            JOIN antennes a ON i.antenne_id = a.id
            WHERE i.statut != 'resolu'
            ORDER BY i.date_creation DESC
            LIMIT 15
        """)
        incidents = cur.fetchall()
        cur.close(); conn.close()

        buffer, c, w, h = _create_pdf_canvas("RAPPORT QUOTIDIEN NOC — Tunisie Télécom Mahdia")
        y = h - 5.0 * cm

        c.setFont("Helvetica-Bold", 12)
        c.drawString(2*cm, y, "Résumé de l'état du réseau")
        y -= 0.8*cm
        c.setFont("Helvetica", 11)
        for line in [
            f"Total antennes supervisées : {total}",
            f"Antennes en alerte ou critique : {alertes}",
            f"Disponibilité globale : {dispo:.2f}%",
            f"Charge CPU moyenne : {avg_cpu:.1f}%",
            f"Température moyenne : {avg_temp:.1f}°C",
        ]:
            c.drawString(2.5*cm, y, line)
            y -= 0.6*cm

        y -= 0.4*cm
        c.setFont("Helvetica-Bold", 12)
        c.drawString(2*cm, y, "Incidents actifs")
        y -= 0.8*cm
        c.setFont("Helvetica", 10)
        if not incidents:
            c.drawString(2.5*cm, y, "Aucun incident actif.")
        for inc in incidents:
            c.drawString(2.5*cm, y, f"• {inc[0]}  [{inc[1]}]  — {inc[4]}  — {str(inc[3])[:16]}")
            y -= 0.6*cm
            if y < 3*cm:
                c.showPage(); y = h - 2*cm

        c.save(); buffer.seek(0)
        return send_file(buffer, as_attachment=True,
                         download_name="rapport_quotidien.pdf",
                         mimetype="application/pdf")
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ════════════════════════════════════════════════════════════════
#  RAPPORT INCIDENTS PDF
# ════════════════════════════════════════════════════════════════

@reports_bp.route("/rapport/incidents", methods=["GET"])
@token_required
def rapport_incidents():
    """Génère et télécharge le rapport PDF complet des incidents."""
    try:
        conn = connecter_base_de_donnees()
        cur  = conn.cursor()
        cur.execute("""
            SELECT i.titre, i.criticite, i.statut, i.description, i.date_creation, a.nom, a.zone
            FROM incidents i
            JOIN antennes a ON i.antenne_id = a.id
            ORDER BY i.date_creation DESC
            LIMIT 50
        """)
        rows = cur.fetchall()
        cur.close(); conn.close()

        buffer, c, w, h = _create_pdf_canvas("RAPPORT DES INCIDENTS — Isolation Forest")
        y = h - 5.0 * cm
        for row in rows:
            titre, crit, statut, desc, date, nom, zone = row
            c.setFont("Helvetica-Bold", 10)
            c.drawString(2*cm, y, f"• {titre}  [{crit.upper()}]  — {nom} ({zone})")
            y -= 0.5*cm
            c.setFont("Helvetica", 9)
            c.drawString(2.5*cm, y, f"{str(date)[:16]}  |  Statut : {statut}")
            y -= 0.5*cm
            if desc:
                c.drawString(2.5*cm, y, (desc[:90] + "…") if len(desc) > 90 else desc)
                y -= 0.5*cm
            y -= 0.3*cm
            if y < 3*cm:
                c.showPage(); y = h - 2*cm

        c.save(); buffer.seek(0)
        return send_file(buffer, as_attachment=True,
                         download_name="rapport_incidents.pdf",
                         mimetype="application/pdf")
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ════════════════════════════════════════════════════════════════
#  RAPPORT ANALYSE IA PDF
# ════════════════════════════════════════════════════════════════

@reports_bp.route("/rapport/ia", methods=["GET"])
@token_required
def rapport_ia():
    """Génère et télécharge le rapport PDF d'analyse Isolation Forest."""
    try:
        anomalies, total_analysed = get_ia_report_anomalies()
        buffer, c, w, h = _create_pdf_canvas("RAPPORT ANALYSE IA — Isolation Forest")
        y = h - 5.0 * cm
        c.setFont("Helvetica-Bold", 12)
        c.drawString(2*cm, y, f"Anomalies détectées : {len(anomalies)} / {total_analysed} sites analysés")
        y -= 1.0*cm
        for _, row in anomalies.head(20).iterrows():
            c.setFont("Helvetica-Bold", 10)
            c.drawString(2*cm, y, f"• {row['nom']}  ({row['zone']})  —  Score IA : {row['score']:.1f}%")
            y -= 0.5*cm
            c.setFont("Helvetica", 9)
            c.drawString(2.5*cm, y,
                f"CPU={row['cpu']:.1f}%  Temp={row['temperature']:.1f}°C  "
                f"Latence={row['latence']:.0f}ms  Dispo={row['disponibilite']:.1f}%")
            y -= 0.7*cm
            if y < 3*cm:
                c.showPage(); y = h - 2*cm

        c.save(); buffer.seek(0)
        return send_file(buffer, as_attachment=True,
                         download_name="rapport_ia.pdf",
                         mimetype="application/pdf")
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ════════════════════════════════════════════════════════════════
#  EXPORT EXCEL & CSV
# ════════════════════════════════════════════════════════════════

@reports_bp.route("/rapport/antennes/excel", methods=["GET"])
@token_required
def rapport_antennes_excel():
    """Exporte les données de toutes les antennes au format Excel."""
    try:
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Alignment

        conn = connecter_base_de_donnees()
        df   = pd.read_sql("""
            SELECT id, nom, zone, type, temperature, cpu, ram, signal,
                   latence, packet_loss, disponibilite, debit, statut, date_mesure::text
            FROM antennes_statut
            ORDER BY id
        """, conn)
        conn.close()

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Antennes Mahdia"
        headers = [
            "ID", "Nom", "Zone", "Type", "Temp (°C)", "CPU (%)", "RAM (%)",
            "Signal (dBm)", "Latence (ms)", "Perte Paquets (%)",
            "Dispo (%)", "Débit (Mbps)", "Statut", "Date Mesure"
        ]
        header_fill = PatternFill(start_color="2563EB", end_color="2563EB", fill_type="solid")
        for col, h in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=h)
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center")
            ws.column_dimensions[cell.column_letter].width = max(12, len(h) + 2)
        for _, row in df.iterrows():
            ws.append(list(row))

        buf = io.BytesIO()
        wb.save(buf); buf.seek(0)
        return send_file(buf, as_attachment=True,
                         download_name="antennes_export.xlsx",
                         mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@reports_bp.route("/reports/csv-data", methods=["GET"])
@token_required
def export_csv_data():
    """Exporte les données au format CSV (antennes, incidents ou mesures)."""
    export_type = request.args.get("type", "antennes")
    try:
        conn = connecter_base_de_donnees()
        if export_type == "incidents":
            df = pd.read_sql("SELECT * FROM incidents ORDER BY date_creation DESC", conn)
        elif export_type == "mesures":
            df = pd.read_sql("SELECT * FROM mesures ORDER BY date_mesure DESC LIMIT 500", conn)
        else:
            df = pd.read_sql("""
                SELECT id, nom, zone, type, temperature, cpu, signal,
                       packet_loss, disponibilite, statut
                FROM antennes_statut
            """, conn)
        conn.close()

        output = io.StringIO()
        df.to_csv(output, index=False)
        output.seek(0)
        mem = io.BytesIO(output.getvalue().encode('utf-8'))
        mem.seek(0)
        return send_file(mem, mimetype="text/csv", as_attachment=True,
                         download_name=f"{export_type}.csv")
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@reports_bp.route("/api/mesures/live", methods=["GET"])
@token_required
def get_mesures_live():
    """Retourne les 50 dernières mesures en temps réel pour les graphiques live."""
    try:
        conn = connecter_base_de_donnees()
        cur  = conn.cursor()
        cur.execute("""
            SELECT m.*, a.nom AS antenne_nom
            FROM mesures m
            JOIN antennes a ON m.antenne_id = a.id
            ORDER BY m.date_mesure DESC
            LIMIT 50
        """)
        data = rows_to_dicts(cur)
        cur.close(); conn.close()
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
