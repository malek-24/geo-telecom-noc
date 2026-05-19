"""
Fonction principale orchestrant l'analyse IA.
Métriques : temperature, cpu, signal, latence, disponibilite
"""
import os
import json
import pandas as pd
import psycopg2
from flask import jsonify

from ia.model      import train_and_predict
from ia.scoring    import calculate_risk_score, determine_statut_final
from ia.diagnostics import diagnostiquer_incident

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:1234@postgres:5432/antennes_mahdia"
)

def _connecter():
    return psycopg2.connect(DATABASE_URL)


def _duree_estimee(criticite: str, risk_score: float) -> int:
    """
    Calcule une durée d'intervention estimée réaliste selon la criticité
    et le score de risque (0-100).
    """
    if criticite == 'critical':
        base = 90
    elif criticite == 'warning':
        base = 45
    else:
        base = 20
    # Le score de risque pondère la durée (+50% max)
    bonus = int((risk_score / 100) * (base * 0.5))
    return base + bonus


def synchroniser_incidents_isolation_forest(conn, df):
    """
    Crée automatiquement des incidents pour les antennes en alerte/critique.
    Résout automatiquement les incidents pour les antennes redevenues normales.
    """
    if df.empty:
        return

    cur = conn.cursor()

    for _, row in df.iterrows():
        ant_id     = int(row["id"])
        statut     = row["new_statut"]
        risk_score = float(row["risk_score"])

        cur.execute(
            "SELECT id FROM incidents WHERE antenne_id = %s AND statut != 'resolu' LIMIT 1",
            (ant_id,)
        )
        active_incident = cur.fetchone()

        if statut in ['alerte', 'critique']:
            if not active_incident:
                titre, description = diagnostiquer_incident(row)
                criticite = 'critical' if statut == 'critique' else 'warning'
                duree     = _duree_estimee(criticite, risk_score)

                metrics = {
                    "temperature":  round(float(row.get("temperature")  or 0), 1),
                    "cpu":          round(float(row.get("cpu")          or 0), 1),
                    "signal":       round(float(row.get("signal")       or -60), 1),
                    "latence":      round(float(row.get("latence")      or 0), 1),
                    "disponibilite": round(float(row.get("disponibilite") or 100), 1),
                    "risk_score":   round(risk_score, 2),
                }

                cur.execute("""
                    INSERT INTO incidents
                        (antenne_id, titre, type_anomalie, description, statut, criticite,
                         source_detection, metriques, risk_score, duree_minutes)
                    VALUES (%s, %s, %s, %s, 'en_cours', %s, 'Isolation Forest', %s::jsonb, %s, %s)
                """, (
                    ant_id, titre, titre, description, criticite,
                    json.dumps(metrics), round(risk_score, 2), duree
                ))
            else:
                inc_id = active_incident[0]
                if statut == 'critique':
                    cur.execute(
                        "UPDATE incidents SET criticite = 'critical' WHERE id = %s",
                        (inc_id,)
                    )

        elif statut == 'normal' and active_incident:
            inc_id = active_incident[0]
            cur.execute(
                "UPDATE incidents SET statut = 'resolu', date_resolution = NOW() WHERE id = %s",
                (inc_id,)
            )

    conn.commit()
    cur.close()


def run_ai_prediction():
    """
    [MOTEUR IA PRINCIPAL]
    Coordonne l'extraction de données, l'inférence IA, et l'impact en base.
    """
    try:
        conn = _connecter()
        df = pd.read_sql("""
            SELECT id, nom, zone, type,
                   temperature, cpu, signal, latence, disponibilite,
                   statut, date_mesure
            FROM antennes_statut
            ORDER BY id
        """, conn)

        if df.empty:
            conn.close()
            return jsonify([])

        # 1. Prédiction IA
        anomaly_output, risk_level = train_and_predict(df)
        df["anomaly_output"] = anomaly_output
        df["risk_level"]     = risk_level

        # 2. Score de risque normalisé [0-100]
        min_score = df["risk_level"].min()
        max_score = df["risk_level"].max()
        df["risk_score"]  = df["risk_level"].apply(
            lambda r: calculate_risk_score(r, min_score, max_score)
        )

        # 3. Statut final
        df["new_statut"] = df["risk_score"].apply(determine_statut_final)

        # 4. Diagnostic automatique
        df["diagnostic"] = df.apply(
            lambda row: diagnostiquer_incident(row)[0] if row["new_statut"] != 'normal' else None,
            axis=1
        )

        # 5. Sauvegarde en base
        cur = conn.cursor()
        for _, row in df.iterrows():
            ant_id = int(row["id"])
            st     = row["new_statut"]
            rs     = float(row["risk_score"])

            cur.execute("""
                UPDATE mesures SET statut = %s, risk_score = %s
                WHERE antenne_id = %s AND date_mesure = %s
            """, (st, rs, ant_id, row["date_mesure"]))

            cur.execute(
                "UPDATE antennes SET statut = %s WHERE id = %s",
                (st, ant_id)
            )

        conn.commit()
        cur.close()

        # 6. Synchronisation des incidents
        synchroniser_incidents_isolation_forest(conn, df)
        conn.close()

        result = df[["id", "risk_score", "new_statut", "diagnostic"]].copy()
        result.rename(columns={"new_statut": "statut"}, inplace=True)
        return jsonify(result.to_dict(orient="records"))

    except Exception as e:
        return jsonify({"error": str(e)}), 500


def get_ia_report_anomalies():
    """Méthode dédiée à la génération du rapport PDF IA."""
    from sklearn.ensemble import IsolationForest

    conn = _connecter()
    df = pd.read_sql("""
        SELECT id, nom, zone, temperature, cpu, latence, disponibilite, statut
        FROM antennes_statut ORDER BY cpu DESC LIMIT 30
    """, conn)
    conn.close()

    if df.empty:
        return pd.DataFrame(), 0

    features = ["temperature", "cpu", "latence", "disponibilite"]
    for col in features:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(df[col].median())

    model = IsolationForest(contamination=0.05, random_state=42)
    df["anomaly"] = model.fit_predict(df[features])
    df["risk"]    = model.decision_function(df[features])
    mn, mx = df["risk"].min(), df["risk"].max()
    df["score"] = 100 * (1 - (df["risk"] - mn) / (mx - mn)) if mx != mn else 0
    anomalies = df[df["anomaly"] == -1].sort_values("score", ascending=False)

    return anomalies, len(df)
