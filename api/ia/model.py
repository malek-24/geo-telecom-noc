"""
Logique d'entraînement et de prédiction du modèle IA (Isolation Forest).
"""
import pandas as pd
from sklearn.ensemble import IsolationForest

# Variables globales utilisées par le modèle
ML_FEATURES = [
    "temperature",
    "cpu",
    "ram",
    "debit",
    "latence",
    "packet_loss",
    "disponibilite",
    "jitter"
]

def train_and_predict(df: pd.DataFrame, contamination_rate=0.08):
    """
    Entraîne le modèle Isolation Forest sur les données en temps réel 
    et calcule le niveau de risque.
    """
    # Nettoyage et imputation
    for col in ML_FEATURES:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(df[col].median())
        
    # Modèle d'anomalies non supervisé
    model = IsolationForest(contamination=contamination_rate, random_state=42)
    
    anomaly_output = model.fit_predict(df[ML_FEATURES])
    risk_level = model.decision_function(df[ML_FEATURES])
    
    return anomaly_output, risk_level
