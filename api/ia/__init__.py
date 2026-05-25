"""
Package ia — Détection d'anomalies GEO-TÉLÉCOM NOC
===================================================
  model.py      → StandardScaler + Isolation Forest
  scoring.py    → Score santé + statut (normal / alerte / critique)
  prediction.py → Pipeline complet + sauvegarde PostgreSQL
  geo_context.py → Écarts par rapport aux antennes voisines (5 km)
  diagnostics.py → Texte d'alerte (métrique la plus anormale)
"""

from ia.model import train_and_predict, get_model, retrain_model, reset_model
from ia.scoring import (
    decision_score_to_health,
    calculate_health_scores_batch,
    determine_statuts_dynamiques,
    determine_statut_final,
    calculate_health_score,
    calculate_risk_score,
)
from ia.diagnostics import diagnostiquer_incident, mettre_a_jour_stats_population
from ia.geo_context import enrichir_avec_contexte_geo, GEO_FEATURES, ML_FEATURES
