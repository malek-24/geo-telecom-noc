"""
database/connection.py — Gestion des connexions PostgreSQL
Fournit des utilitaires propres pour se connecter à la base de données
et convertir les résultats en dictionnaires Python.
"""
import psycopg2
from utils.globals import DATABASE_URL


def connecter_base_de_donnees():
    """Retourne une nouvelle connexion PostgreSQL."""
    return psycopg2.connect(DATABASE_URL)


def rows_to_dicts(cur):
    """
    Convertit tous les résultats d'un curseur psycopg2 en liste de dictionnaires.
    Doit être appelé UNE SEULE FOIS après l'exécution de la requête SQL.
    """
    if cur.description is None:
        return []
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]
