"""
model.py — Isolation Forest (sklearn)
======================================
PFE Licence — Réseaux & Télécommunications

Étapes :
  1. Charger les 2000 dernières mesures normales (PostgreSQL)
  2. StandardScaler + IsolationForest.fit()
  3. predict() → anomalie oui/non + score de décision

Réentraînement : toutes les 24 h ou 100 nouvelles mesures normales.
Bloqué si force_no_retrain=True (admin, IoT, test jury).
"""

import os
import numpy as np
import pandas as pd
import joblib
from datetime import datetime, timedelta
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from ia.geo_context import enrichir_avec_contexte_geo, GEO_FEATURES, ML_FEATURES

MODEL_PATH  = "/tmp/iso_forest_model.pkl"
SCALER_PATH = "/tmp/iso_forest_scaler.pkl"

RETRAIN_INTERVAL_HOURS = 24
RETRAIN_THRESHOLD      = 100
MIN_SAMPLES_TRAIN      = 200
MAX_SAMPLES_TRAIN      = 2000

IF_N_ESTIMATORS  = 200
IF_CONTAMINATION = 0.005
IF_RANDOM_STATE  = 42

_model_cache       = None
_scaler_cache      = None
_last_train_time   = None
_measures_at_train = 0


def _charger_historique(conn) -> pd.DataFrame:
    """2000 dernières mesures normales — fenêtre glissante."""
    return pd.read_sql(f"""
        SELECT
            m.antenne_id AS id,
            m.temperature, m.cpu, m.signal, m.latence, m.disponibilite,
            a.latitude, a.longitude
        FROM mesures m
        JOIN antennes a ON a.id = m.antenne_id
        WHERE (m.statut IS NULL OR m.statut = 'normal')
          AND m.statut NOT IN ('alerte', 'critique', 'analyse_ia_en_cours')
          AND m.temperature IS NOT NULL AND m.cpu IS NOT NULL
          AND m.signal IS NOT NULL AND m.latence IS NOT NULL
          AND m.disponibilite IS NOT NULL
        ORDER BY m.date_mesure DESC
        LIMIT {MAX_SAMPLES_TRAIN}
    """, conn)


def _fallback_synthetique() -> pd.DataFrame:
    """Données de démarrage si la base contient peu de mesures."""
    np.random.seed(42)
    n = 1200
    data = {
        "id": np.arange(n),
        "temperature":   np.clip(np.random.normal(28.0, 1.2, n), 25.0, 32.0),
        "cpu":           np.clip(np.random.normal(40.0, 2.0, n), 36.0, 44.0),
        "signal":        np.clip(np.random.normal(-65.0, 2.0, n), -71.0, -59.0),
        "latence":       np.clip(np.random.normal(15.0, 0.8, n), 13.5, 16.5),
        "disponibilite": np.clip(np.random.normal(99.0, 0.5, n), 97.0, 100.0),
        "latitude":      np.full(n, 35.5),
        "longitude":     np.full(n, 11.0),
        "delta_temp_voisins": np.zeros(n),
        "delta_cpu_voisins": np.zeros(n),
        "delta_signal_voisins": np.zeros(n),
        "delta_lat_voisins": np.zeros(n),
        "delta_dispo_voisins": np.zeros(n),
        "nb_voisins_anomalies": np.zeros(n),
    }
    return pd.DataFrame(data)


def _compter_mesures_normales(conn) -> int:
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM mesures WHERE statut IS NULL OR statut = 'normal'")
    n = cur.fetchone()[0]
    cur.close()
    return int(n)


def _entrainer_modele(df_train: pd.DataFrame):
    global _model_cache, _scaler_cache, _last_train_time

    df_enrichi = enrichir_avec_contexte_geo(df_train, rayon_km=5.0)
    for feat in GEO_FEATURES:
        if feat not in df_enrichi.columns:
            df_enrichi[feat] = 0.0
        df_enrichi[feat] = pd.to_numeric(df_enrichi[feat], errors="coerce").fillna(0.0)

    X = df_enrichi[GEO_FEATURES].values
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    model = IsolationForest(
        contamination=IF_CONTAMINATION,
        n_estimators=IF_N_ESTIMATORS,
        random_state=IF_RANDOM_STATE,
        n_jobs=-1,
    )
    model.fit(X_scaled)

    try:
        joblib.dump(model, MODEL_PATH)
        joblib.dump(scaler, SCALER_PATH)
    except Exception as e:
        print(f"[IA] Sauvegarde modèle : {e}")

    _model_cache = model
    _scaler_cache = scaler
    _last_train_time = datetime.now()
    print(f"[IA] Modèle entraîné sur {len(df_train)} mesures.")
    return model, scaler


def get_model(conn=None, force_no_retrain=False):
    global _model_cache, _scaler_cache, _last_train_time, _measures_at_train

    if not force_no_retrain and _model_cache is not None and conn is not None:
        besoin = False
        if _last_train_time and (datetime.now() - _last_train_time) > timedelta(hours=RETRAIN_INTERVAL_HOURS):
            besoin = True
        if not besoin:
            nb = _compter_mesures_normales(conn)
            if nb - _measures_at_train >= RETRAIN_THRESHOLD:
                besoin = True
                _measures_at_train = nb
        if besoin:
            retrain_model(conn)

    if _model_cache is not None:
        return _model_cache, _scaler_cache

    if os.path.exists(MODEL_PATH) and os.path.exists(SCALER_PATH):
        try:
            _model_cache = joblib.load(MODEL_PATH)
            _scaler_cache = joblib.load(SCALER_PATH)
            _last_train_time = datetime.now()
            return _model_cache, _scaler_cache
        except Exception:
            pass

    if conn is not None:
        try:
            df_hist = _charger_historique(conn)
            if len(df_hist) >= MIN_SAMPLES_TRAIN:
                _measures_at_train = _compter_mesures_normales(conn)
                return _entrainer_modele(df_hist)
        except Exception as e:
            print(f"[IA] Lecture BD : {e}")

    return _entrainer_modele(_fallback_synthetique())


def retrain_model(conn):
    global _measures_at_train
    df_hist = _charger_historique(conn)
    if len(df_hist) >= MIN_SAMPLES_TRAIN:
        _measures_at_train = _compter_mesures_normales(conn)
        _entrainer_modele(df_hist)


def train_and_predict(df: pd.DataFrame, conn=None, force_no_retrain=False):
    """Isolation Forest : retourne (anomalies bool[], scores float[])."""
    df = df.copy()
    for col in ML_FEATURES:
        df[col] = pd.to_numeric(df[col], errors="coerce")
        df[col] = df[col].fillna(df[col].median())

    df = enrichir_avec_contexte_geo(df, rayon_km=5.0)
    for feat in GEO_FEATURES:
        if feat not in df.columns:
            df[feat] = 0.0
        df[feat] = pd.to_numeric(df[feat], errors="coerce").fillna(0.0)

    model, scaler = get_model(conn, force_no_retrain=force_no_retrain)
    X_scaled = scaler.transform(df[GEO_FEATURES].values)

    preds = model.predict(X_scaled)
    scores = model.decision_function(X_scaled)
    return [p == -1 for p in preds], scores.tolist()


def reset_model():
    global _model_cache, _scaler_cache, _last_train_time, _measures_at_train
    _model_cache = _scaler_cache = _last_train_time = None
    _measures_at_train = 0
    for path in (MODEL_PATH, SCALER_PATH):
        try:
            if os.path.exists(path):
                os.remove(path)
        except Exception:
            pass
