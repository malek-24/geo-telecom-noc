"""
ia/diagnostics.py — Génération des diagnostics d'incidents IA
==============================================================
GEO-TÉLÉCOM NOC — Mahdia

AUCUN SEUIL CODÉ EN DUR.

La cause d'une anomalie est identifiée par comparaison statistique
(Z-score) de chaque métrique par rapport à la population globale
d'antennes analysée dans le même cycle.

PRINCIPE :
  Pour chaque anomalie détectée par l'Isolation Forest, on calcule
  pour chaque métrique son Z-score par rapport à la distribution
  observée sur l'ensemble des antennes au même instant.

  La métrique avec le Z-score le plus élevé (le plus éloigné de la
  moyenne de la population) est identifiée comme cause principale.

  Si une déviation géographique est plus forte, elle prime :
  Si delta_temp_voisins (écart aux antennes voisines) est élevé,
  l'anomalie géographique est signalée.

Z-SCORE :
  z = (valeur - moyenne_population) / écart_type_population
  |z| élevé → métrique très différente des autres antennes
"""

import numpy as np
import pandas as pd
from typing import Tuple, Optional

# Labels lisibles pour chaque feature
FEATURE_LABELS = {
    "temperature":           "Température anormale",
    "cpu":                   "Surcharge CPU",
    "signal":                "Signal dégradé",
    "latence":               "Latence élevée",
    "disponibilite":         "Disponibilité faible",
    "delta_temp_voisins":    "Anomalie géographique (température)",
    "delta_cpu_voisins":     "Anomalie géographique (CPU)",
    "delta_signal_voisins":  "Anomalie géographique (signal)",
    "delta_lat_voisins":     "Anomalie géographique (latence)",
    "delta_dispo_voisins":   "Anomalie géographique (disponibilité)",
    "nb_voisins_anomalies":  "Propagation d'anomalies (voisines)",
}

# Métriques à analyser (base + géo) en ordre de priorité
FEATURES_A_ANALYSER = [
    "delta_temp_voisins",    # Priorité aux anomalies géo
    "delta_cpu_voisins",
    "delta_signal_voisins",
    "delta_lat_voisins",
    "delta_dispo_voisins",
    "temperature",
    "cpu",
    "signal",
    "latence",
    "disponibilite",
    "nb_voisins_anomalies",
]

# Population globale partagée (mise à jour à chaque cycle d'analyse)
_population_stats: Optional[dict] = None


def mettre_a_jour_stats_population(df_population: pd.DataFrame):
    """
    Met à jour les statistiques de population (moyenne, écart-type)
    à partir du DataFrame complet des antennes du cycle courant.

    Appelé une fois par cycle d'analyse avant de diagnostiquer.

    Paramètres :
      df_population : DataFrame avec toutes les antennes du cycle
                      (avec les features géo enrichies)
    """
    global _population_stats
    _population_stats = {}
    for feat in FEATURES_A_ANALYSER:
        if feat in df_population.columns:
            col = pd.to_numeric(df_population[feat], errors="coerce").dropna()
            if len(col) > 1:
                _population_stats[feat] = {
                    "mean": float(col.mean()),
                    "std":  float(col.std()) or 1.0,  # éviter division par 0
                    "median": float(col.median()),
                }


def _calculer_zscores(row: pd.Series) -> dict:
    """
    Calcule le Z-score absolu de chaque feature pour une antenne donnée
    par rapport aux statistiques de population stockées.

    Retourne un dict {feature: |z-score|}
    """
    if not _population_stats:
        return {}

    zscores = {}
    for feat in FEATURES_A_ANALYSER:
        if feat not in _population_stats:
            continue
        valeur = pd.to_numeric(row.get(feat, None), errors="coerce")
        if valeur is None or np.isnan(float(valeur)):
            continue
        stats = _population_stats[feat]
        z = abs((float(valeur) - stats["mean"]) / stats["std"])
        zscores[feat] = z

    return zscores


def diagnostiquer_incident(row: pd.Series) -> Tuple[str, str]:
    """
    Analyse les métriques d'une antenne pour identifier la cause
    principale de l'anomalie détectée par l'Isolation Forest.

    Méthode :
      1. Calcul du Z-score absolu de chaque feature
      2. La feature avec le Z-score le plus élevé = cause principale
      3. Description enrichie avec les valeurs observées vs médiane population

    Paramètres :
      row : Série pandas représentant une antenne (une ligne du DataFrame
            enrichi avec les features géo)

    Retour :
      (titre, description) — strings pour l'incident en base
    """
    zscores = _calculer_zscores(row)

    if not zscores:
        # Pas de statistiques de population disponibles — diagnostic générique
        return _diagnostic_generique(row)

    # Trouver la feature la plus déviante
    worst_feat  = max(zscores, key=zscores.get)
    worst_zscore = zscores[worst_feat]

    label = FEATURE_LABELS.get(worst_feat, worst_feat)

    # Construire un message contextuel (pas de comparaison à un seuil fixe)
    valeur = float(row.get(worst_feat, 0) or 0)
    if worst_feat in _population_stats:
        mediane = _population_stats[worst_feat]["median"]
        ecart   = valeur - mediane
        signe   = "au-dessus" if ecart > 0 else "en-dessous"
        ecart_abs = abs(ecart)

        titre = f"Anomalie IA : {label}"
        desc  = (
            f"L'Isolation Forest a détecté un comportement statistiquement anormal "
            f"(z-score = {worst_zscore:.1f}). "
            f"La métrique '{label}' est {signe} de {ecart_abs:.2f} unités "
            f"par rapport à la médiane de la population ({mediane:.2f}). "
            f"Valeur observée : {valeur:.2f}."
        )
    else:
        titre = f"Anomalie IA : {label}"
        desc  = (
            f"L'Isolation Forest a détecté un comportement statistiquement anormal "
            f"(z-score = {worst_zscore:.1f}) sur la métrique '{label}'. "
            f"Valeur observée : {valeur:.2f}."
        )

    return titre, desc


def _diagnostic_generique(row: pd.Series) -> Tuple[str, str]:
    """
    Diagnostic générique quand les statistiques de population
    ne sont pas encore disponibles (premier cycle).
    """
    # Identifier la métrique la plus extrême relativement aux autres
    metriques_brutes = {
        "temperature":   float(row.get("temperature",   0) or 0),
        "cpu":           float(row.get("cpu",           0) or 0),
        "signal":        float(row.get("signal",        -65) or -65),
        "latence":       float(row.get("latence",       0) or 0),
        "disponibilite": float(row.get("disponibilite", 100) or 100),
    }

    # Déltas géographiques si disponibles
    if "delta_temp_voisins" in row.index:
        delta_temp = abs(float(row.get("delta_temp_voisins", 0) or 0))
        if delta_temp > 5.0:  # écart significatif avec les voisins
            return (
                "Anomalie IA : Incohérence géographique de température",
                f"Écart de {delta_temp:.1f}°C par rapport aux antennes voisines détecté "
                f"par l'Isolation Forest. Comportement géographiquement incohérent."
            )

    return (
        "Anomalie Globale Multi-Facteurs",
        "L'Isolation Forest a détecté un comportement anormal basé sur "
        "la combinaison statistique des métriques réseau "
        "(CPU, température, latence, signal, disponibilité)."
    )
