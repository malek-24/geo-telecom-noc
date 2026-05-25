"""
prediction.py — Moteur IA (orchestration)
==========================================
PFE Licence — Réseaux & Télécommunications

Pipeline pour le jury :
  Mesure → PostgreSQL → Isolation Forest → Score santé → État → Dashboard

  - antenne_id fourni : une seule antenne mise à jour (admin, IoT, simulateur)
  - force_no_retrain  : True pour les démos, False pour le simulateur (apprentissage)
"""

import json
import os
import numpy as np
import pandas as pd
import psycopg2
from flask import jsonify

from ia.model       import train_and_predict, retrain_model, get_model
from ia.scoring     import (
    calculate_health_scores_batch,
    determine_statuts_dynamiques,
    decision_score_to_health,
    ecart_significatif,
    mesures_dans_plage_normale,
    SEUIL_NORMAL,
)
from ia.diagnostics import diagnostiquer_incident, mettre_a_jour_stats_population
from ia.geo_context import enrichir_avec_contexte_geo, ML_FEATURES, GEO_FEATURES

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:1234@postgres:5432/antennes_mahdia"
)


def _connecter():
    """Ouvre une connexion PostgreSQL."""
    return psycopg2.connect(DATABASE_URL)


def _duree_estimee(criticite: str, health_score: float) -> int:
    """
    Durée d'intervention estimée (minutes) selon la criticité et le score santé.
    Plus le score est bas (anomalie prononcée), plus l'intervention est longue.
    """
    base = 90 if criticite == 'critical' else 45
    bonus = int(((100 - health_score) / 100) * (base * 0.5))
    return base + bonus


def bootstrap_reseau_normal(conn=None):
    """
    État initial au démarrage (121 Normal, 0 Alerte, 0 Critique) :
      - clôture les incidents ouverts (résidus de tests)
      - met à jour uniquement la DERNIÈRE mesure de chaque antenne (historique conservé)
      - réinitialise les statuts antennes
      - réentraîne l'Isolation Forest sur le comportement normal
    """
    close_conn = False
    if conn is None:
        conn = _connecter()
        close_conn = True

    try:
        cur = conn.cursor()

        # Supprimer les résidus d'anciens tests
        cur.execute("""
            UPDATE incidents
            SET statut = 'resolu', date_resolution = NOW()
            WHERE statut != 'resolu'
        """)
        nb_incidents = cur.rowcount

        # Dernière mesure de chaque antenne → Normal
        cur.execute("""
            UPDATE mesures m
            SET statut = 'normal', risk_score = 85.0
            FROM (
                SELECT DISTINCT ON (antenne_id) id
                FROM mesures
                ORDER BY antenne_id, date_mesure DESC
            ) latest
            WHERE m.id = latest.id
        """)
        nb_mesures = cur.rowcount

        cur.execute("UPDATE antennes SET statut = 'normal' WHERE statut != 'maintenance'")
        conn.commit()
        cur.close()

        from ia.model import reset_model, retrain_model
        reset_model()
        retrain_model(conn)

        if close_conn:
            conn.close()

        print(
            f"[IA] Bootstrap réseau propre — "
            f"{nb_incidents} incident(s) clôturé(s), "
            f"{nb_mesures} mesure(s) → Normal, modèle IF réentraîné."
        )
        return True

    except Exception as e:
        print(f"[IA ERREUR] bootstrap_reseau_normal : {e}")
        import traceback
        traceback.print_exc()
        if close_conn and conn:
            conn.close()
        return False


def get_etat_ia_snapshot():
    """
    Retourne l'état IA actuel en base (lecture seule).
    Utilisé par GET /predict pour la carte sans recalcul global.
    """
    try:
        conn = _connecter()
        df = pd.read_sql("""
            SELECT
                s.id,
                s.statut,
                COALESCE(s.risk_score, 85.0) AS risk_score,
                CASE WHEN s.statut IN ('alerte', 'critique') THEN 1 ELSE 0 END AS anomaly
            FROM antennes_statut s
            ORDER BY s.id
        """, conn)
        conn.close()
        return jsonify(df.to_dict(orient="records"))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def _affiner_detection_apres_if(df: pd.DataFrame) -> pd.DataFrame:
    """Annule un faux positif IF si les métriques sont encore dans une variation normale."""
    df = df.copy()
    for idx, row in df.iterrows():
        severe = ecart_significatif(
            row.get("temperature"),
            row.get("cpu"),
            row.get("signal"),
            row.get("latence"),
            row.get("disponibilite"),
        )

        if severe:
            continue  # garder le verdict Isolation Forest

        routine = mesures_dans_plage_normale(
            row.get("temperature"),
            row.get("cpu"),
            row.get("signal"),
            row.get("latence"),
            row.get("disponibilite"),
        )
        if not routine:
            continue  # ex. 35 °C : laisser l'IF décider (alerte progressive)

        # Variation normale (28.3 °C, CPU 42 %, etc.) : corriger le faux positif
        df.at[idx, "anomalie_if"]  = False
        df.at[idx, "health_score"] = max(float(row["health_score"]), SEUIL_NORMAL + 5.0)
        df.at[idx, "new_statut"]   = "normal"
        df.at[idx, "diagnostic"]   = None

    return df


def synchroniser_incidents_isolation_forest(conn, df: pd.DataFrame):
    """
    Crée ou résout automatiquement les incidents pour les antennes du DataFrame.

    - Si statut = alerte/critique et pas d'incident actif → crée un incident
    - Si statut = normal et incident actif → résout l'incident
    - Si statut = critique et incident existant → met à jour la criticité

    Paramètres :
      conn : connexion PostgreSQL
      df   : DataFrame avec les colonnes : id, new_statut, health_score, ...
    """
    if df.empty:
        return

    cur = conn.cursor()

    for _, row in df.iterrows():
        ant_id       = int(row["id"])
        statut       = row["new_statut"]
        health_score = float(row["health_score"])

        # Chercher un incident actif pour cette antenne
        cur.execute(
            "SELECT id FROM incidents WHERE antenne_id = %s AND statut != 'resolu' LIMIT 1",
            (ant_id,)
        )
        incident_actif = cur.fetchone()

        if statut in ('alerte', 'critique'):
            if not incident_actif:
                # Créer un nouvel incident
                titre, description = diagnostiquer_incident(row)
                criticite = 'critical' if statut == 'critique' else 'warning'
                duree     = _duree_estimee(criticite, health_score)

                metriques = _metriques_incident_depuis_ligne(row)
                metriques["health_score"] = round(health_score, 2)

                cur.execute("""
                    INSERT INTO incidents
                        (antenne_id, titre, type_anomalie, description, statut,
                         criticite, source_detection, metriques, risk_score, duree_minutes)
                    VALUES (%s, %s, %s, %s, 'en_cours', %s,
                            'Isolation Forest (non supervisé)', %s::jsonb, %s, %s)
                """, (
                    ant_id, titre, titre, description, criticite,
                    json.dumps(metriques), round(health_score, 2), duree
                ))
            else:
                # Incident existant : mettre à jour la criticité si nécessaire
                inc_id = incident_actif[0]
                if statut == 'critique':
                    cur.execute(
                        "UPDATE incidents SET criticite = 'critical' WHERE id = %s",
                        (inc_id,)
                    )

        elif statut == 'normal' and incident_actif:
            # Antenne revenue à la normale → résoudre l'incident
            inc_id = incident_actif[0]
            cur.execute(
                "UPDATE incidents SET statut = 'resolu', date_resolution = NOW() WHERE id = %s",
                (inc_id,)
            )

    conn.commit()
    cur.close()


def _metriques_incident_depuis_ligne(row) -> dict:
    """Construit le JSON métriques stocké sur l'incident."""
    health_score = float(row.get("health_score") or row.get("risk_score") or 0)
    return {
        "temperature":    round(float(row.get("temperature")   or 0), 1),
        "cpu":            round(float(row.get("cpu")           or 0), 1),
        "signal":         round(float(row.get("signal")        or -65), 1),
        "latence":        round(float(row.get("latence")       or 0), 1),
        "disponibilite":  round(float(row.get("disponibilite") or 100), 1),
        "health_score":   round(health_score, 2),
        "anomalie_if":    bool(row.get("anomalie_if", False)),
        "decision_score": round(float(row.get("decision_score") or 0), 4),
    }


def finalize_incident_resolution(incident_id: int) -> dict:
    """
    Résolution manuelle d'un incident — Règles métier NOC :

    DONNÉES HISTORIQUES (jamais supprimées) :
      - Toutes les mesures passées restent intactes en base
      - Tous les scores santé historiques sont conservés
      - Tous les graphiques restent disponibles
      - Les données de rapport ne sont pas effacées

    ACTIONS À LA RÉSOLUTION :
      1. incident.statut         = 'resolu'  + date_resolution = NOW()
      2. Alertes actives         → supprimées (incidents en_cours de cette antenne)
      3. antenne.statut          = 'normal'  (mise à jour immédiate)
      4. score_sante             = 95        (sur la DERNIÈRE mesure uniquement)
      5. Dashboard               → reflète immédiatement l'état résolu
      6. Validation IA optionnelle : si l'anomalie persiste, un nouvel incident est créé
    """
    try:
        conn = _connecter()
        cur = conn.cursor()

        # ── Récupérer l'antenne associée ────────────────────────────
        cur.execute(
            "SELECT antenne_id FROM incidents WHERE id = %s",
            (incident_id,),
        )
        row = cur.fetchone()
        if not row:
            cur.close()
            conn.close()
            return {
                "success": False,
                "error": "Incident introuvable",
                "resolution_validee": False,
            }

        antenne_id = int(row[0])

        # ── Étape 1 : Clôturer l'incident résolu ───────────────────
        cur.execute("""
            UPDATE incidents
            SET statut = 'resolu', date_resolution = NOW()
            WHERE id = %s
        """, (incident_id,))

        # ── Étape 2 : Supprimer TOUTES les alertes actives de cette antenne ─
        # (incidents en_cours hors l'incident qu'on vient de résoudre)
        cur.execute("""
            UPDATE incidents
            SET statut = 'resolu', date_resolution = NOW()
            WHERE antenne_id = %s
              AND statut != 'resolu'
              AND id != %s
        """, (antenne_id, incident_id))
        nb_alertes_supprimees = cur.rowcount

        # ── Étape 3 : antenne.statut = 'normal' — mise à jour immédiate ─
        cur.execute(
            "UPDATE antennes SET statut = 'normal' WHERE id = %s",
            (antenne_id,)
        )

        # ── Étape 4 : score_sante = 95 sur la DERNIÈRE mesure ──────
        # Seule la DERNIÈRE mesure est mise à jour → historique conservé intégralement
        cur.execute("""
            UPDATE mesures
            SET statut     = 'normal',
                risk_score = 95.0
            WHERE id = (
                SELECT id FROM mesures
                WHERE antenne_id = %s
                ORDER BY date_mesure DESC
                LIMIT 1
            )
        """, (antenne_id,))

        conn.commit()
        cur.close()

        print(
            f"[IA] ✅ Résolution manuelle — incident #{incident_id}, "
            f"antenne {antenne_id} → normal (score=95.0), "
            f"{nb_alertes_supprimees} alerte(s) active(s) supprimée(s). "
            f"Historique des mesures, graphiques et rapports conservés intégralement."
        )

        # ── Étape 5 : Validation IA — vérifie si l'anomalie persiste ──
        # force_no_retrain=True : le modèle ne se réentraîne pas lors d'une résolution
        # sync_incidents=True   : si anomalie toujours présente → nouvel incident créé
        conn.close()
        run_ai_prediction(
            antenne_id=antenne_id,
            force_no_retrain=True,
            sync_incidents=True,
        )

        # ── Étape 6 : Lire l'état final après analyse IA ───────────
        conn = _connecter()
        cur = conn.cursor()
        cur.execute("""
            SELECT statut, COALESCE(risk_score, 95.0) AS risk_score
            FROM antennes_statut
            WHERE id = %s
        """, (antenne_id,))
        ant_row = cur.fetchone()

        if not ant_row:
            cur.close()
            conn.close()
            # L'antenne a quand même été mise à jour (normal + 95) à l'étape 3-4
            return {
                "success": True,
                "id": incident_id,
                "statut": "resolu",
                "antenne_statut": "normal",
                "risk_score": 95.0,
                "resolution_validee": True,
                "donnees_historiques_conservees": True,
                "message": (
                    "Résolution confirmée. Antenne → normal, score santé = 95. "
                    "Historique des mesures, graphiques et scores conservés."
                ),
            }

        statut_antenne = ant_row[0]
        health_score   = float(ant_row[1])

        # Vérifier si l'IA a recréé un incident (anomalie persistante)
        cur.execute("""
            SELECT id FROM incidents
            WHERE antenne_id = %s AND statut != 'resolu'
            ORDER BY date_creation DESC
            LIMIT 1
        """, (antenne_id,))
        nouvel_incident = cur.fetchone()
        cur.close()
        conn.close()

        # ── Cas 1 : Résolution confirmée — antenne normale ──────────
        if statut_antenne == "normal":
            return {
                "success": True,
                "id": incident_id,
                "statut": "resolu",
                "antenne_statut": "normal",
                "risk_score": round(health_score, 2),
                "resolution_validee": True,
                "donnees_historiques_conservees": True,
                "message": (
                    "✅ Résolution confirmée — antenne → normal, score santé = 95. "
                    "Historique des mesures, graphiques et scores conservés intégralement."
                ),
            }

        # ── Cas 2 : Anomalie persistante — nouvel incident créé par l'IA ─
        print(
            f"[IA] ⚠️ Anomalie persistante — incident #{incident_id} résolu, "
            f"nouvel incident #{nouvel_incident[0] if nouvel_incident else '?'} "
            f"— antenne {antenne_id} → {statut_antenne}"
        )
        return {
            "success": True,
            "id": incident_id,
            "statut": "resolu",
            "antenne_statut": statut_antenne,
            "nouvel_incident_id": nouvel_incident[0] if nouvel_incident else None,
            "risk_score": round(health_score, 2),
            "resolution_validee": False,
            "donnees_historiques_conservees": True,
            "message": (
                "⚠️ Anomalie toujours détectée par l'IA : un nouvel incident a été créé. "
                f"État antenne : {statut_antenne}. "
                "Historique conservé intégralement."
            ),
        }

    except Exception as e:
        print(f"[IA ERREUR] finalize_incident_resolution : {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e),
            "resolution_validee": False,
        }


def run_ai_prediction(antenne_id=None, force_no_retrain=False, sync_incidents=True):
    """
    [MOTEUR IA PRINCIPAL]

    Pipeline complet d'analyse Isolation Forest.

    Paramètres :
      antenne_id       : int ou None
                         - None     → analyse TOUTES les antennes (cycle simulateur)
                         - int      → analyse UNIQUEMENT cette antenne (modification admin/IoT)
                           Les autres antennes gardent leur statut inchangé.
      force_no_retrain : bool (défaut=False)
                         - True  → bloque le réentraînement automatique
                           Utilisé pour toutes les actions de démonstration.
                         - False → réentraînement automatique si critères atteints
      sync_incidents   : bool (défaut=True)
                         - True  → crée/résout les incidents (admin, IoT, test)
                         - False → met à jour les statuts sans toucher aux incidents

    Exemple d'utilisation ciblée :
      run_ai_prediction(antenne_id=13, force_no_retrain=True)
      → Analyse uniquement TT-013
      → Toutes les autres antennes : statut inchangé

    Retour : Flask Response (JSON)
    """
    try:
        conn = _connecter()

        # ── Étape 1 : Lecture de TOUTES les antennes ───────────────
        # On lit toujours tout le réseau pour calculer le contexte géographique
        # (déltas voisins). C'est nécessaire pour que le score IF soit précis.
        df = pd.read_sql("""
            SELECT
                s.id, a.nom, a.zone, a.type,
                s.temperature, s.cpu, s.signal, s.latence, s.disponibilite,
                s.statut, s.date_mesure,
                a.latitude, a.longitude
            FROM antennes_statut s
            JOIN antennes a ON a.id = s.id
            ORDER BY s.id
        """, conn)

        if df.empty:
            conn.close()
            return jsonify([])

        # ── Étape 2 : Isolation Forest → anomalie + score ──────────
        # force_no_retrain bloque le réentraînement si action de démo
        anomaly_flags, decision_scores = train_and_predict(
            df, conn=conn, force_no_retrain=force_no_retrain
        )
        df["anomalie_if"]    = anomaly_flags
        df["decision_score"] = decision_scores

        # ── Étape 3 : Enrichissement géographique ──────────────────
        df = enrichir_avec_contexte_geo(df, rayon_km=5.0, col_anomalie="anomalie_if")

        # ── Étape 4 : Statistiques population (pour diagnostics) ───
        mettre_a_jour_stats_population(df)

        # ── Étape 5 : Score de santé (sigmoïde du score IF) ────────
        # Pénalité voisins uniquement si écart significatif (pas sur MRRW normal)
        nb_voisins_raw = (
            df["nb_voisins_anomalies"].astype(int).tolist()
            if "nb_voisins_anomalies" in df.columns
            else [0] * len(df)
        )
        nb_voisins = []
        for (_, row), nv in zip(df.iterrows(), nb_voisins_raw):
            if ecart_significatif(
                row.get("temperature"), row.get("cpu"),
                row.get("signal"), row.get("latence"), row.get("disponibilite"),
            ):
                nb_voisins.append(nv)
            else:
                nb_voisins.append(0)

        df["health_score"] = calculate_health_scores_batch(
            decision_scores=decision_scores,
            nb_voisins_anomalies=nb_voisins,
        )

        # ── Étape 6 : Statut final (basé sur le score santé) ───────
        # Normal ≥ 70 / Alerte [40-70[ / Critique < 40
        statuts = determine_statuts_dynamiques(
            health_scores=df["health_score"].tolist(),
            anomaly_flags=anomaly_flags,
        )
        df["new_statut"] = statuts

        # ── Étape 6b : Validation écart significatif (faux positifs uniquement) ─
        df = _affiner_detection_apres_if(df)

        # ── Étape 7 : Diagnostic (Z-score) ─────────────────────────
        df["diagnostic"] = df.apply(
            lambda row: diagnostiquer_incident(row)[0]
            if row["new_statut"] != 'normal' else None,
            axis=1
        )

        # ── Étape 8 : Sélection des antennes à mettre à jour ───────
        # Si antenne_id fourni → mettre à jour UNIQUEMENT cette antenne
        # Si non → mettre à jour TOUTES les antennes
        if antenne_id is not None:
            df_update = df[df["id"] == antenne_id].copy()
            if df_update.empty:
                conn.close()
                return jsonify({"error": f"Antenne {antenne_id} introuvable"}), 404
            mode = f"ciblée (antenne {antenne_id})"
        else:
            df_update = df.copy()
            mode = f"globale ({len(df)} antennes)"

        # ── Étape 9 : Sauvegarde en base ───────────────────────────
        cur = conn.cursor()
        for _, row in df_update.iterrows():
            ant_id = int(row["id"])
            st     = row["new_statut"]
            hs     = float(row["health_score"])

            # Mettre à jour le statut de la dernière mesure
            cur.execute("""
                UPDATE mesures SET statut = %s, risk_score = %s
                WHERE id = (
                    SELECT id FROM mesures
                    WHERE antenne_id = %s
                    ORDER BY date_mesure DESC
                    LIMIT 1
                )
            """, (st, hs, ant_id))

            # Mettre à jour le statut de l'antenne
            cur.execute(
                "UPDATE antennes SET statut = %s WHERE id = %s",
                (st, ant_id)
            )

        conn.commit()
        cur.close()

        if antenne_id is not None:
            print("[Dashboard] Dernière mesure :", antenne_id)

        # ── Étape 10 : Synchronisation des incidents (ciblé uniquement) ─
        if sync_incidents:
            synchroniser_incidents_isolation_forest(conn, df_update)
        conn.close()

        # ── Résultat ───────────────────────────────────────────────
        result = df_update[[
            "id", "health_score", "new_statut", "anomalie_if",
            "diagnostic", "decision_score",
        ]].copy()
        result.rename(columns={
            "new_statut":   "statut",
            "health_score": "risk_score",
        }, inplace=True)
        # Compatibilité carte : anomaly=1 si alerte/critique
        result["anomaly"] = result.apply(
            lambda r: 1 if r["statut"] in ("alerte", "critique") else 0,
            axis=1,
        )

        # Log résumé
        n_normal   = (result["statut"] == "normal").sum()
        n_alerte   = (result["statut"] == "alerte").sum()
        n_critique = (result["statut"] == "critique").sum()
        scores     = df_update["decision_score"].values
        retrain_info = "bloqué (démo)" if force_no_retrain else "auto"
        print(
            f"[IA] Analyse {mode} — "
            f"{n_normal} normales, {n_alerte} alertes, {n_critique} critiques | "
            f"Réentraînement={retrain_info} | "
            f"score_if: min={scores.min():.3f} max={scores.max():.3f}"
        )

        return jsonify(result.to_dict(orient="records"))

    except Exception as e:
        print(f"[IA ERREUR] run_ai_prediction : {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


def get_ia_report_anomalies():
    """
    Méthode pour la génération du rapport PDF IA.
    Retourne les antennes en anomalie avec leurs scores IF.
    """
    conn = _connecter()

    df = pd.read_sql("""
        SELECT
            s.id, s.nom, s.zone,
            s.temperature, s.cpu, s.signal, s.latence, s.disponibilite,
            s.statut, s.risk_score,
            a.latitude, a.longitude
        FROM antennes_statut s
        JOIN antennes a ON a.id = s.id
        ORDER BY s.id
        LIMIT 50
    """, conn)

    if df.empty:
        conn.close()
        return pd.DataFrame(), 0

    # Nettoyage
    for col in ML_FEATURES:
        df[col] = pd.to_numeric(df[col], errors="coerce")
        df[col] = df[col].fillna(df[col].median())

    # Enrichissement géo
    df = enrichir_avec_contexte_geo(df, rayon_km=5.0)
    for feat in GEO_FEATURES:
        if feat not in df.columns:
            df[feat] = 0.0
        df[feat] = pd.to_numeric(df[feat], errors="coerce").fillna(0.0)

    # Prédiction IF (sans réentraînement — rapport uniquement)
    model, scaler = get_model(conn, force_no_retrain=True)
    conn.close()

    X = df[GEO_FEATURES].values
    X_scaled = scaler.transform(X)

    predictions     = model.predict(X_scaled)
    decision_scores = model.decision_function(X_scaled)

    df["anomaly"]      = predictions
    df["score"]        = decision_scores
    df["health_score"] = [decision_score_to_health(s) for s in decision_scores]

    anomalies = df[df["anomaly"] == -1].sort_values("health_score", ascending=True)
    return anomalies, len(df)
