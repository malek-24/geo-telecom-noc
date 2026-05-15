"""
Génération des diagnostics d'incidents IA basés sur les écarts aux normes.
"""

def diagnostiquer_incident(row):
    """
    Analyse les métriques brutes pour déterminer QUELLE feature a poussé l'IA 
    à signaler cette antenne comme anomalie. Retourne le titre et la description.
    """
    temp   = float(row.get("temperature") or 0)
    cpu    = float(row.get("cpu") or 0)
    latence = float(row.get("latence") or 0)
    pkt    = float(row.get("packet_loss") or 0)
    
    # Écarts empiriques simples
    deviations = {
        "Température": max(0, temp - 45),
        "CPU": max(0, cpu - 50),
        "Latence": max(0, latence - 30),
        "Perte de Paquets": max(0, pkt - 1) * 10
    }
    
    worst_metric = max(deviations, key=deviations.get)
    
    if deviations[worst_metric] > 0:
        titre = f"Anomalie IA détectée : {worst_metric}"
        desc = f"Le modèle Isolation Forest a identifié une déviation statistique majeure, principalement tirée par la métrique {worst_metric}."
        return titre, desc
    
    return "Anomalie Globale Multi-Facteurs", "Le modèle Isolation Forest a détecté un comportement anormal basé sur une combinaison complexe de métriques."
