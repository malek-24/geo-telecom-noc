"""
Fonction principale orchestrant l'analyse IA.
Gère la récupération depuis PostgreSQL, le traitement, et la sauvegarde.
"""
import os
import json
import random
import pandas as pd
import psycopg2
from flask import jsonify

from ia.model import train_and_predict
from ia.scoring import calculate_risk_score, determine_statut_final
from ia.diagnostics import diagnostiquer_incident

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:1234@postgres:5432/antennes_mahdia"
)

def _connecter_base_de_donnees():
    return psycopg2.connect(DATABASE_URL)

def synchroniser_incidents_isolation_forest(conn, df):
    """
    Crée automatiquement des incidents pour les antennes en alerte/critique.
    Résout automatiquement les incidents pour les antennes redevenues normales.
    """
    if df.empty:
        return

    cur = conn.cursor()
    
    for _, row in df.iterrows():
        ant_id = int(row["id"])
        statut = row["new_statut"]
        risk_score = row["risk_score"]
        
        # Vérifie l'existence d'un incident actif
        cur.execute("SELECT id FROM incidents WHERE antenne_id = %s AND statut != 'resolu' LIMIT 1", (ant_id,))
        active_incident = cur.fetchone()

        if statut in ['alerte', 'critique']:
            if not active_incident:
                titre, description = diagnostiquer_incident(row)
                criticite = 'critical' if statut == 'critique' else 'warning'
                metrics = {
                    "temperature":  float(row.get("temperature") or 0),
                    "cpu":          float(row.get("cpu") or 0),
                    "ram":          float(row.get("ram") or 0),
                    "throughput":   float(row.get("debit") or 0),
                    "latency":      float(row.get("latence") or 0),
                    "packet_loss":  float(row.get("packet_loss") or 0),
                    "availability": float(row.get("disponibilite") or 0),
                    "risk_score":   round(float(risk_score), 2),
                }
                
                cur.execute("""
                    INSERT INTO incidents
                        (antenne_id, titre, type_anomalie, description, statut, criticite,
                         source_detection, metriques, duree_minutes)
                    VALUES (%s, %s, %s, %s, 'en_cours', %s, 'Isolation Forest', %s::jsonb, %s)
                """, (
                    ant_id, titre, titre, description, criticite, json.dumps(metrics), random.randint(30, 120)
                ))
            else:
                inc_id = active_incident[0]
                if statut == 'critique':
                    cur.execute("UPDATE incidents SET criticite = 'critical' WHERE id = %s", (inc_id,))
                
        elif statut == 'normal':
            if active_incident:
                inc_id = active_incident[0]
                cur.execute("UPDATE incidents SET statut = 'resolu', date_resolution = NOW() WHERE id = %s", (inc_id,))
                
    conn.commit()
    cur.close()

def run_ai_prediction():
    """
    [MOTEUR IA PRINCIPAL] 
    Coordonne l'extraction de données, l'inférence IA, et l'impact en base.
    """
    try:
        conn = _connecter_base_de_donnees()
        df = pd.read_sql("""
            SELECT id, nom, zone, type, temperature, cpu, ram, debit, latence,
                   packet_loss, disponibilite, jitter, statut, date_mesure
            FROM antennes_statut
            ORDER BY id
        """, conn)
        
        if df.empty:
            conn.close()
            return jsonify([])

        # 1. Modélisation et Prédiction
        anomaly_output, risk_level = train_and_predict(df)
        df["anomaly_output"] = anomaly_output
        df["risk_level"] = risk_level
        
        # 2. Score de Risque
        min_score = df["risk_level"].min()
        max_score = df["risk_level"].max()
        df["risk_score"] = df["risk_level"].apply(lambda r: calculate_risk_score(r, min_score, max_score))
        
        # 3. Évaluation Statut Final
        df["new_statut"] = df["risk_score"].apply(determine_statut_final)
        
        # 4. Diagnostic Automatique
        df["diagnostic"] = df.apply(lambda row: diagnostiquer_incident(row)[0] if row["new_statut"] != 'normal' else None, axis=1)

        # 5. Sauvegarde Base de Données (Single Source of Truth)
        cur = conn.cursor()
        for _, row in df.iterrows():
            ant_id = int(row["id"])
            nom_ant = row["nom"]
            st = row["new_statut"]
            rs = float(row["risk_score"])
            
            cur.execute("""
                UPDATE mesures 
                SET statut = %s, risk_score = %s 
                WHERE antenne_id = %s AND date_mesure = %s
            """, (st, rs, ant_id, row["date_mesure"]))
            
            cur.execute("""
                UPDATE antennes 
                SET statut = %s
                WHERE id = %s
            """, (st, ant_id))
            
        conn.commit()
        cur.close()

        # 6. Synchronisation Incidents
        synchroniser_incidents_isolation_forest(conn, df)
        conn.close()

        result = df[["id", "risk_score", "new_statut", "diagnostic"]].copy()
        result.rename(columns={"new_statut": "statut"}, inplace=True)
        return jsonify(result.to_dict(orient="records"))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def get_ia_report_anomalies():
    """
    Méthode dédiée à la génération du rapport PDF IA.
    """
    from sklearn.ensemble import IsolationForest
    
    conn = _connecter_base_de_donnees()
    df = pd.read_sql("""
        SELECT id, nom, zone, temperature, cpu, latence, disponibilite, statut
        FROM antennes_statut ORDER BY cpu DESC LIMIT 30
    """, conn)
    conn.close()
    
    if df.empty:
        return pd.DataFrame(), 0
        
    model = IsolationForest(contamination=0.05, random_state=42)
    features = ["temperature", "cpu", "latence", "disponibilite"]
    for col in features:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(df[col].median())
        
    df["anomaly"] = model.fit_predict(df[features])
    df["risk"] = model.decision_function(df[features])
    mn, mx = df["risk"].min(), df["risk"].max()
    df["score"] = 100 * (1 - (df["risk"] - mn) / (mx - mn)) if mx != mn else 0
    anomalies = df[df["anomaly"] == -1].sort_values("score", ascending=False)
    
    return anomalies, len(df)
