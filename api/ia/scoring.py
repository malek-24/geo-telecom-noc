"""
Logique de calcul du score de risque et de détermination du statut IA.
"""

def calculate_risk_score(risk_level, min_score, max_score):
    """
    Normalise la fonction de décision (decision_function) de l'Isolation Forest
    en un pourcentage de risque compréhensible (0-100%).
    """
    if max_score != min_score:
        return 100 * (1 - (risk_level - min_score) / (max_score - min_score))
    return 0

def determine_statut_final(risk_score):
    """
    Applique la logique métier pour traduire le score de risque IA 
    en statut système compréhensible.
    """
    if risk_score >= 70:
        return 'critique'
    elif risk_score >= 40:
        return 'alerte'
    else:
        return 'normal'
