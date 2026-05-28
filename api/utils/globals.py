import os
import time

# Antennes récemlement résolues manuellement : l'IA globale ne doit pas
# recréer d'incident ni repasser en alerte/critique pendant la fenêtre.
RESOLUTION_MANUELLE_GRACE = {}  # antenne_id -> timestamp Unix de fin
RESOLUTION_GRACE_SECONDES = 120


def marquer_resolution_manuelle(antenne_id: int, duree_sec: int = RESOLUTION_GRACE_SECONDES) -> None:
    RESOLUTION_MANUELLE_GRACE[int(antenne_id)] = time.time() + duree_sec


def en_grace_resolution(antenne_id: int) -> bool:
    fin = RESOLUTION_MANUELLE_GRACE.get(int(antenne_id))
    if fin is None:
        return False
    if time.time() > fin:
        RESOLUTION_MANUELLE_GRACE.pop(int(antenne_id), None)
        return False
    return True

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:1234@postgres:5432/antennes_mahdia")
JWT_SECRET = os.getenv("JWT_SECRET", "pfe-sig-mahdia-jwt-secret-2024")
JWT_EXPIRATION_HOURS = 24

ADMIN_LOGS = [
    {"id": 1, "heure": "2026-05-08 21:00", "utilisateur": "Malek Admin", "action": "Connexion réussie", "statut": "Succès"},
    {"id": 2, "heure": "2026-05-08 19:15", "utilisateur": "Ingénieur N1", "action": "Détection anomalie IA", "statut": "Warning"},
    {"id": 3, "heure": "2026-05-08 18:30", "utilisateur": "Système", "action": "Génération rapport auto", "statut": "Succès"},
]

SYSTEM_SETTINGS = {
    "update_freq": 5,
    "temp_threshold": 45,   # Seuil critique DHT11 : 45°C (max physique = 50°C)
    "cpu_threshold": 85,
    "ia_active": True,
    "alerts_active": True,
    "report_freq": "daily",
    "maintenance_mode": False
}
