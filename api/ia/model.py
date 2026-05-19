"""
Logique d'entraînement et de prédiction du modèle IA (Isolation Forest).
Métriques conservées : temperature, cpu, signal, latence, disponibilite
"""
import pandas as pd
from sklearn.ensemble import IsolationForest

# ── 5 métriques conservées ────────────────────────────────────────
ML_FEATURES = [
    "temperature",
    "cpu",
    "signal",
    "latence",
    "disponibilite",
]

def train_and_predict(df: pd.DataFrame, contamination_rate=0.08):
    """
    Entraîne le modèle Isolation Forest sur les données en temps réel
    et calcule le niveau de risque.
    """
    # Nettoyage et imputation par la médiane
    for col in ML_FEATURES:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(df[col].median())

    model = IsolationForest(contamination=contamination_rate, random_state=42)
    anomaly_output = model.fit_predict(df[ML_FEATURES])
    risk_level     = model.decision_function(df[ML_FEATURES])

    return anomaly_output, risk_level
