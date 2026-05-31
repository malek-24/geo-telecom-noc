"""
routes/ia.py — Endpoints REST pour le moteur IA (Isolation Forest non supervisé)
==================================================================================
GEO-TÉLÉCOM NOC — Mahdia
PFE Licence — Réseaux & Télécommunications 2025/2026

Routes exposées :
  GET  /predict              — Analyse IA authentifiée (dashboard)
  GET  /internal/predict     — Analyse IA interne (simulateur Docker)
  POST /ia/retrain           — Réentraînement forcé (admin uniquement)
  GET  /ia/model/info        — Informations sur le modèle actuel
  POST /ia/reset             — Réinitialisation complète du modèle (admin)
  POST /test-ia              — Scénarios de démonstration (jury) ; via Nginx : /api/test-ia
"""
import os
from datetime import datetime
from flask import Blueprint, request, jsonify

from auth.decorators import token_required, role_required
from ia.prediction import run_ai_prediction, get_etat_ia_snapshot
from ia.model import retrain_model, reset_model
from database.connection import connecter_base_de_donnees


ia_bp = Blueprint('ia_bp', __name__)


@ia_bp.route("/predict", methods=["GET"])
@token_required
def predict():
    """
    [AUTHENTIFIÉ] État IA temps réel (lecture seule depuis la base).
    Ne relance pas d'analyse globale — évite les faux positifs sur le réseau sain.
    La carte fusionne ces données avec GET /antennes.
    """
    return get_etat_ia_snapshot()


@ia_bp.route("/internal/predict", methods=["GET"])
def get_internal_ia_predictions():
    """
    [INTERNE] Analyse IA après nouvelles mesures.
    Query : ?source=simulation (cycle global 10 s, toutes antennes)
            ?antenne_id=42 (IoT / ciblage unitaire)
    """
    antenne_id = request.args.get("antenne_id", type=int)

    # simulation → réentraînement glissant autorisé (fenêtre 2000 mesures normales)
    # admin/iot/test → force_no_retrain via appels Python directs
    source = request.args.get("source", "simulation")
    allow_retrain = source == "simulation"

    # Cycle simulateur (10 s) : analyse globale sans antenne_id
    # IoT / admin : antenne_id ciblé
    return run_ai_prediction(
        antenne_id=antenne_id,
        force_no_retrain=not allow_retrain,
        sync_incidents=True,
    )


@ia_bp.route("/ia/retrain", methods=["POST"])
@role_required('administrateur', 'ingenieur_reseau')
def force_retrain():
    """
    [ADMIN] Force le réentraînement immédiat du modèle Isolation Forest
    sur les données historiques actuelles en base.

    Utile quand l'administrateur veut forcer l'intégration de données récentes.
    Cet endpoint est le SEUL moyen de forcer un réentraînement manuellement.
    Le réentraînement automatique reste géré par les critères temporel/volume.
    """
    try:
        conn = connecter_base_de_donnees()

        import pandas as pd
        df_count = pd.read_sql(
            "SELECT COUNT(*) AS nb FROM mesures WHERE statut IS DISTINCT FROM 'critique'",
            conn
        )
        nb_mesures = int(df_count["nb"].iloc[0])

        retrain_model(conn)
        conn.close()

        return jsonify({
            "success":    True,
            "message":    f"Modèle Isolation Forest réentraîné sur {nb_mesures} mesures historiques.",
            "nb_mesures": nb_mesures,
            "heure":      datetime.now().strftime("%H:%M:%S"),
        })

    except Exception as e:
        print(f"[IA ERREUR] /ia/retrain : {e}")
        return jsonify({"error": str(e)}), 500


@ia_bp.route("/ia/info", methods=["GET"])
@token_required
def get_ia_info():
    """
    Informations pédagogiques sur le moteur IA (page « IA & Machine Learning »).
    """
    try:
        import ia.model as _ia_model
        from ia.geo_context import ML_FEATURES

        conn = connecter_base_de_donnees()
        import pandas as pd

        total = int(pd.read_sql("SELECT COUNT(*) AS n FROM antennes", conn)["n"].iloc[0])
        df_stat = pd.read_sql(
            "SELECT statut, COUNT(*) AS n FROM antennes_statut GROUP BY statut", conn
        )
        by_status = dict(zip(df_stat["statut"], df_stat["n"]))
        anomalies = int(by_status.get("alerte", 0) + by_status.get("critique", 0))
        taux_anomalie = round((anomalies / total) * 100, 1) if total else 0.0

        last_train = _ia_model._last_train_time
        conn.close()

        return jsonify({
            "modele": "Isolation Forest",
            "type": "Apprentissage non supervisé",
            "fenetre": _ia_model.MAX_SAMPLES_TRAIN,
            "features": list(ML_FEATURES),
            "antennes": total,
            "anomalies": anomalies,
            "taux_anomalie": taux_anomalie,
            "dernier_entrainement": (
                last_train.strftime("%d/%m/%Y %H:%M")
                if last_train else "Non encore entraîné"
            ),
            "n_estimators": _ia_model.IF_N_ESTIMATORS,
            "contamination": _ia_model.IF_CONTAMINATION,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@ia_bp.route("/ia/model/info", methods=["GET"])
@token_required
def get_model_info():
    """
    [AUTHENTIFIÉ] Retourne les informations sur le modèle IA actuel.

    Affiche dans le dashboard :
      - Date du dernier entraînement
      - Nombre de mesures utilisées
      - Paramètres du modèle
      - Statut du réentraînement automatique
    """
    try:
        import ia.model as _ia_model
        from ia.geo_context import GEO_FEATURES

        conn = connecter_base_de_donnees()
        import pandas as pd
        df = pd.read_sql("SELECT COUNT(*) AS nb FROM mesures", conn)
        nb_total = int(df["nb"].iloc[0])
        conn.close()

        model_sur_disque = os.path.exists(_ia_model.MODEL_PATH)
        last_train       = _ia_model._last_train_time
        measures_at_train = _ia_model._measures_at_train

        return jsonify({
            "modele":           "Isolation Forest (sklearn)",
            "apprentissage":    "Non supervisé — données historiques réelles",
            "contamination":    str(_ia_model.IF_CONTAMINATION),
            "n_estimators":     _ia_model.IF_N_ESTIMATORS,
            "nb_features":      len(GEO_FEATURES),
            "features":         list(GEO_FEATURES),
            "rayon_voisinage":  "5 km (Haversine)",
            "dernier_entrainement": (
                last_train.strftime("%Y-%m-%d %H:%M:%S")
                if last_train else "Non encore entraîné"
            ),
            "mesures_a_lentrainement": measures_at_train,
            "mesures_totales_bd":      nb_total,
            "nouvelles_mesures":       max(0, nb_total - measures_at_train),
            "seuil_retrain_volume":    _ia_model.RETRAIN_THRESHOLD,
            "seuil_retrain_heures":    _ia_model.RETRAIN_INTERVAL_HOURS,
            "modele_sur_disque":       model_sur_disque,
            "seuils_codes_en_dur":     False,
            "score_statut":            "Sigmoïde IF → score santé 0-100 (seuils: 70/40)",
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@ia_bp.route("/ia/reset", methods=["POST"])
@role_required('administrateur')
def force_reset():
    """
    [ADMIN] Réinitialise complètement le modèle IA.
    Le prochain cycle déclenchera un nouvel entraînement
    sur toutes les données historiques disponibles.
    """
    try:
        reset_model()
        return jsonify({
            "success": True,
            "message": "Modèle réinitialisé. Le prochain cycle déclenchera un réentraînement complet.",
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@ia_bp.route("/test-ia", methods=["POST"])
@token_required
def force_ia_incident():
    """
    [DÉMO] Injecte des métriques anormales sur une antenne pour déclencher
    une anomalie IA — utilisé pour les démonstrations devant le jury.

    RÈGLE : force_no_retrain=True
      → Le modèle NE SE RÉENTRAÎNE PAS lors d'un test.
      → Il prédit uniquement sur le modèle déjà entraîné.
      → Seule l'antenne injectée est analysée (recalcul ciblé).

    Types de scénarios disponibles :
      - "surchauffe" : température très élevée + CPU saturé
      - "surcharge"  : CPU maximal + latence critique
      - "panne"      : signal perdu + disponibilité très basse

    Body JSON :
    {
        "type": "surchauffe",
        "antenne_id": 13   (optionnel — aléatoire si absent)
    }
    """
    data          = request.get_json() or {}
    type_incident = data.get("type", "surchauffe")

    # Valeurs de démonstration — clairement anormales pour l'IF
    metriques = {
        "temp": 28.0, "cpu": 40.0, "signal": -65.0,
        "latence": 15.0, "dispo": 99.0
    }

    if type_incident == "surchauffe":
        metriques["temp"] = 72.0    # Bien au-delà du comportement appris
        metriques["cpu"]  = 96.0
    elif type_incident == "surcharge":
        metriques["cpu"]     = 99.0
        metriques["temp"]    = 55.0
        metriques["latence"] = 280.0
        metriques["dispo"]   = 70.0
    elif type_incident == "panne":
        metriques["dispo"]   = 45.0
        metriques["signal"]  = -118.0
        metriques["latence"] = 450.0

    try:
        conn = connecter_base_de_donnees()
        cur  = conn.cursor()

        # Utiliser l'antenne_id fourni, ou en choisir une au hasard
        ant_id_force = data.get("antenne_id")
        if ant_id_force:
            ant_id = int(ant_id_force)
        else:
            cur.execute("SELECT id FROM antennes ORDER BY RANDOM() LIMIT 1")
            ant_id = cur.fetchone()[0]

        # Insérer la mesure anormale
        cur.execute("""
            INSERT INTO mesures
                (antenne_id, temperature, cpu, signal,
                 latence, disponibilite, statut, date_mesure)
            VALUES (%s, %s, %s, %s, %s, %s, 'analyse_ia_en_cours', NOW())
        """, (
            ant_id,
            metriques["temp"],    metriques["cpu"],   metriques["signal"],
            metriques["latence"], metriques["dispo"]
        ))
        conn.commit()
        cur.close(); conn.close()

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    # ── Analyse IA ciblée + force_no_retrain ─────────────────────
    # Seule cette antenne est analysée. Le modèle ne se réentraîne pas.
    try:
        response = run_ai_prediction(antenne_id=ant_id, force_no_retrain=True)
        data_ia  = response.get_json()

        statut_ia   = "en_cours"
        risque_ia   = 0.0
        anomalie_ia = False

        if isinstance(data_ia, list) and data_ia:
            r           = data_ia[0]
            statut_ia   = r.get("statut",     "en_cours")
            risque_ia   = r.get("risk_score", 0.0)
            anomalie_ia = r.get("anomalie_if", False)

        return jsonify({
            "success":    True,
            "antenne_id": ant_id,
            "type":       type_incident,
            "message":    f"Scénario '{type_incident}' injecté sur l'antenne {ant_id}. "
                          f"Résultat IA : {statut_ia}.",
            "metriques":  metriques,
            "statut_ia":  statut_ia,
            "risk_score": risque_ia,
            "anomalie":   anomalie_ia,
        })

    except Exception as e:
        return jsonify({
            "success":    True,
            "antenne_id": ant_id,
            "message":    f"Scénario '{type_incident}' injecté. IA en cours d'analyse.",
            "metriques":  metriques,
            "error_ia":   str(e),
        })
