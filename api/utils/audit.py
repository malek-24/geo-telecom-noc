"""
audit.py — Journal d'audit persistant (PostgreSQL)
"""
from flask import request, has_request_context


def _client_ip() -> str:
    if not has_request_context():
        return ""
    return (request.headers.get("X-Forwarded-For") or request.remote_addr or "").split(",")[0].strip()


def enregistrer_audit(
    conn,
    utilisateur: str,
    action: str,
    cible: str = "",
    type_objet: str = "",
    valeur_avant: str = "",
    valeur_apres: str = "",
    adresse_ip: str = None,
) -> None:
    """Ajoute une entrée au journal d'audit."""
    ip = adresse_ip if adresse_ip is not None else _client_ip()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO audit_logs (
                utilisateur, action, cible, type_objet,
                valeur_avant, valeur_apres, adresse_ip
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                str(utilisateur or "système"),
                str(action),
                str(cible or ""),
                str(type_objet or ""),
                str(valeur_avant or "")[:2000],
                str(valeur_apres or "")[:2000],
                str(ip or "")[:64],
            ),
        )
        cur.close()
    except Exception as e:
        print(f"[AUDIT] Erreur enregistrement : {e}")
