
import os

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
    "temp_threshold": 75,
    "cpu_threshold": 85,
    "ia_active": True,
    "alerts_active": True,
    "report_freq": "daily",
    "maintenance_mode": False
}
