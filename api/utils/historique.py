"""
historique.py — Historique des changements d'état des antennes
"""
from utils.audit import enregistrer_audit


def lire_statut_antenne(cur, antenne_id: int) -> str:
    cur.execute("SELECT statut FROM antennes WHERE id = %s", (int(antenne_id),))
    row = cur.fetchone()
    return (row[0] if row and row[0] else "normal")


def enregistrer_changement_etat(
    conn, antenne_id: int, ancien_etat: str, nouvel_etat: str
) -> None:
    """Enregistre une transition d'état si elle change réellement."""
    ancien = (ancien_etat or "normal").strip().lower()
    nouveau = (nouvel_etat or "normal").strip().lower()
    if ancien == nouveau:
        return
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO historique_etats (antenne_id, ancien_etat, nouvel_etat)
            VALUES (%s, %s, %s)
            """,
            (int(antenne_id), ancien, nouveau),
        )
        cur.execute("SELECT nom FROM antennes WHERE id = %s", (int(antenne_id),))
        nom_row = cur.fetchone()
        cible = nom_row[0] if nom_row else f"ID {antenne_id}"
        enregistrer_audit(
            conn,
            "système",
            "Changement état antenne",
            cible=cible,
            type_objet="antenne",
            valeur_avant=ancien,
            valeur_apres=nouveau,
        )
        cur.close()
    except Exception as e:
        print(f"[HISTORIQUE] Erreur enregistrement : {e}")
