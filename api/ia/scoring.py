"""
scoring.py — Du score Isolation Forest au statut antenne
========================================================
PFE Licence — Réseaux & Télécommunications

Chaîne expliquée au jury :
  1. Isolation Forest produit un score (positif = normal, négatif = anormal)
  2. Sigmoïde → score santé entre 0 et 100
  3. Seuils fixes : ≥70 normal | 40–69 alerte | <40 critique
  4. Filtre optionnel si les métriques sont encore dans une variation normale
"""

import numpy as np
from typing import List

# ── Conversion score IF → score santé ───────────────────────────
SIGMOID_K = 8.0
SEUIL_NORMAL = 70.0
SEUIL_ALERTE = 40.0

# Plages de variation normale du réseau (MRRW + DHT11 25–32 °C)
PLAGES = {
    "temperature":   (25.0, 32.0),
    "cpu":           (36.0, 44.0),
    "signal":        (-71.0, -59.0),
    "latence":       (13.5, 16.5),
    "disponibilite": (97.0, 100.0),
}

# Valeurs de référence pour détecter un écart important (admin, panne, DHT11 chaud)
REF = {"temperature": 28.0, "cpu": 40.0, "signal": -65.0, "latence": 15.0, "disponibilite": 99.0}


def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + np.exp(-SIGMOID_K * x))


def decision_score_to_health(decision_score: float, nb_voisins_anomalies: int = 0) -> float:
    """Convertit le score Isolation Forest en score de santé (0–100)."""
    ratio = _sigmoid(decision_score)
    if nb_voisins_anomalies > 0:
        ratio *= 1.0 - min(0.15, nb_voisins_anomalies * 0.03)
    return round(ratio * 100.0, 2)


def calculate_health_scores_batch(
    decision_scores: List[float],
    nb_voisins_anomalies: List[int] = None,
) -> List[float]:
    if nb_voisins_anomalies is None:
        nb_voisins_anomalies = [0] * len(decision_scores)
    return [
        decision_score_to_health(ds, nv)
        for ds, nv in zip(decision_scores, nb_voisins_anomalies)
    ]


def determine_statut_final(health_score: float, anomalie_if: bool = False) -> str:
    """Statut à partir du score santé uniquement (seuils 70 / 40)."""
    if health_score < SEUIL_ALERTE:
        return "critique"
    if health_score < SEUIL_NORMAL:
        return "alerte"
    return "normal"


def determine_statuts_dynamiques(
    health_scores: List[float],
    anomaly_flags: List[bool],
) -> List[str]:
    return [determine_statut_final(s) for s in health_scores]


def mesures_dans_plage_normale(temperature, cpu, signal, latence, disponibilite) -> bool:
    """True si toutes les métriques sont dans les plages habituelles (réseau vivant)."""
    try:
        v = {
            "temperature": float(temperature),
            "cpu": float(cpu),
            "signal": float(signal),
            "latence": float(latence),
            "disponibilite": float(disponibilite),
        }
        for cle, (vmin, vmax) in PLAGES.items():
            if not (vmin <= v[cle] <= vmax):
                return False
        return True
    except (TypeError, ValueError):
        return False


def ecart_significatif(temperature, cpu, signal, latence, disponibilite) -> bool:
    """
    True si une métrique est très éloignée du réseau sain.
    Exemples : CPU 95 %, signal -110 dBm, latence 250 ms, température 42 °C+.
    """
    try:
        t, c, s, l, d = (
            float(temperature), float(cpu), float(signal),
            float(latence), float(disponibilite),
        )
    except (TypeError, ValueError):
        return False

    if abs(t - REF["temperature"]) / REF["temperature"] > 0.35:
        return True
    if abs(c - REF["cpu"]) / REF["cpu"] > 0.35:
        return True
    if abs(s - REF["signal"]) > 12.0:
        return True
    if abs(l - REF["latence"]) / REF["latence"] > 0.80:
        return True
    if (REF["disponibilite"] - d) > 4.0:
        return True
    return False


# Alias conservés pour compatibilité
PLAGES_NORMALES = PLAGES


def calculate_health_score(
    temperature=0.0, cpu=0.0, signal=0.0, latence=0.0, disponibilite=100.0,
    anomalie_if=False, decision_score=0.0, nb_voisins_anomalies=0,
) -> float:
    return decision_score_to_health(decision_score, nb_voisins_anomalies)


def calculate_risk_score(health_score: float, *args, **kwargs) -> float:
    return health_score
