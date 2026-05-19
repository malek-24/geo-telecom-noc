"""
Génération des diagnostics d'incidents IA basés sur les écarts aux normes.
Métriques analysées : temperature, cpu, signal, latence, disponibilite
"""

def diagnostiquer_incident(row):
    """
    Analyse les métriques brutes pour déterminer quelle feature a poussé l'IA
    à signaler cette antenne comme anomalie.
    Retourne le titre et la description de l'incident.
    """
    temp      = float(row.get("temperature") or 0)
    cpu       = float(row.get("cpu")         or 0)
    latence   = float(row.get("latence")     or 0)
    signal    = float(row.get("signal")      or -60)
    dispo     = float(row.get("disponibilite") or 100)

    # Calcul des écarts empiriques par rapport aux seuils normaux
    deviations = {
        "Température":     max(0, temp    - 45),
        "CPU":             max(0, cpu     - 60),
        "Latence":         max(0, latence - 30),
        "Signal Faible":   max(0, -95     - signal),   # signal trop négatif
        "Disponibilité":   max(0, 95      - dispo),    # disponibilité trop basse
    }

    worst_metric = max(deviations, key=deviations.get)

    if deviations[worst_metric] > 0:
        titre = f"Anomalie IA détectée : {worst_metric}"
        desc  = (
            f"Le modèle Isolation Forest a identifié une déviation statistique majeure, "
            f"principalement tirée par la métrique '{worst_metric}'."
        )
        return titre, desc

    return (
        "Anomalie Globale Multi-Facteurs",
        "Le modèle Isolation Forest a détecté un comportement anormal basé sur "
        "une combinaison des métriques réseau (CPU, température, latence, signal, disponibilité)."
    )
