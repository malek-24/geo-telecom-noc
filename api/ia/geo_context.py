"""
geo_context.py — Contexte géographique (Mahdia)
================================================
Pour chaque antenne : écart entre ses métriques et la médiane des voisines
dans un rayon de 5 km (Haversine). Entrées supplémentaires pour l'Isolation Forest.
"""

import math
import numpy as np
import pandas as pd

# ── Rayon de voisinage (en kilomètres) ────────────────────────────
RAYON_VOISINAGE_KM = 5.0

# ── Features de base analysées ────────────────────────────────────
ML_FEATURES = [
    "temperature",
    "cpu",
    "signal",
    "latence",
    "disponibilite",
]

# ── Features enrichies avec contexte géo ──────────────────────────
GEO_FEATURES = ML_FEATURES + [
    "delta_temp_voisins",
    "delta_cpu_voisins",
    "delta_signal_voisins",
    "delta_lat_voisins",
    "delta_dispo_voisins",
    "nb_voisins_anomalies",
]


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calcule la distance en kilomètres entre deux points GPS
    via la formule de Haversine.

    Paramètres :
      lat1, lon1 : coordonnées du point 1 (degrés décimaux)
      lat2, lon2 : coordonnées du point 2 (degrés décimaux)

    Retour :
      distance en kilomètres (float)
    """
    R = 6371.0  # rayon de la Terre en km
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2) ** 2 + \
        math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2

    return R * 2 * math.asin(math.sqrt(a))


def enrichir_avec_contexte_geo(
    df: pd.DataFrame,
    rayon_km: float = RAYON_VOISINAGE_KM,
    col_anomalie: str = "anomalie_if",
) -> pd.DataFrame:
    """
    Enrichit le DataFrame des antennes avec des features géographiques.

    Pour chaque antenne, calcule l'écart de chaque métrique par rapport
    à la médiane de ses voisines dans un rayon `rayon_km`.

    Si une antenne n'a aucune voisine dans le rayon, les deltas valent 0.0
    (pas d'information géo disponible — neutre pour l'IF).

    Paramètres :
      df         : DataFrame contenant au minimum les colonnes :
                   id, latitude, longitude + ML_FEATURES
                   et optionnellement `anomalie_if` (bool)
      rayon_km   : rayon de voisinage en km (défaut: 5 km)
      col_anomalie: colonne booléenne indiquant si l'antenne est en anomalie

    Retour :
      df enrichi avec les colonnes GEO_FEATURES supplémentaires
    """
    df = df.copy()

    # Vérifier que les coordonnées sont disponibles
    has_coords = ("latitude" in df.columns and "longitude" in df.columns
                  and df["latitude"].notna().any())

    # Valeur par défaut si pas de coordonnées : déltas = 0 (neutre)
    for feat in ML_FEATURES:
        df[f"delta_{_short(feat)}_voisins"] = 0.0
    df["nb_voisins_anomalies"] = 0

    if not has_coords:
        return df

    # Convertir les coordonnées en float
    lats = df["latitude"].astype(float).values
    lons = df["longitude"].astype(float).values
    ids  = df["id"].values
    n    = len(df)

    # Matrice d'anomalies existantes (avant ce cycle si disponible)
    if col_anomalie in df.columns:
        anomalies = df[col_anomalie].fillna(False).astype(bool).values
    else:
        anomalies = np.zeros(n, dtype=bool)

    # Métriques sous forme de matrice numpy pour efficacité
    metriques = {}
    for feat in ML_FEATURES:
        metriques[feat] = pd.to_numeric(df[feat], errors="coerce").fillna(0).values

    # Calcul des déltas pour chaque antenne
    delta_results = {feat: np.zeros(n) for feat in ML_FEATURES}
    nb_anomalies_voisins = np.zeros(n, dtype=int)

    for i in range(n):
        voisins_idx = []
        for j in range(n):
            if i == j:
                continue
            dist = haversine_km(lats[i], lons[i], lats[j], lons[j])
            if dist <= rayon_km:
                voisins_idx.append(j)

        if not voisins_idx:
            # Pas de voisins → déltas restent à 0 (neutre)
            continue

        for feat in ML_FEATURES:
            valeurs_voisins = metriques[feat][voisins_idx]
            mediane_voisins = float(np.median(valeurs_voisins))
            delta_results[feat][i] = metriques[feat][i] - mediane_voisins

        nb_anomalies_voisins[i] = int(np.sum(anomalies[voisins_idx]))

    # Injecter dans le DataFrame
    df["delta_temp_voisins"]   = delta_results["temperature"]
    df["delta_cpu_voisins"]    = delta_results["cpu"]
    df["delta_signal_voisins"] = delta_results["signal"]
    df["delta_lat_voisins"]    = delta_results["latence"]
    df["delta_dispo_voisins"]  = delta_results["disponibilite"]
    df["nb_voisins_anomalies"] = nb_anomalies_voisins

    return df


def _short(feature_name: str) -> str:
    """Raccourcit le nom de la feature pour les colonnes delta."""
    mapping = {
        "temperature":   "temp",
        "cpu":           "cpu",
        "signal":        "signal",
        "latence":       "lat",
        "disponibilite": "dispo",
    }
    return mapping.get(feature_name, feature_name)
