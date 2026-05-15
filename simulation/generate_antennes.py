"""
generate_antennes.py  —  Script de peuplement initial
Plateforme NOC Tunisie Télécom — Gouvernorat de Mahdia

IMPORTANT : Génère exactement 120 antennes fixes réparties
dans 14 zones géographiques réelles de Mahdia.
Ne jamais modifier les coordonnées sans régénérer la BD.
"""

import random
import psycopg2

# Graine aléatoire fixe — garantit des positions stables entre redémarrages
random.seed(42)

# =============================================================
# 14 ZONES GÉOGRAPHIQUES — total = exactement 120 antennes
# (nom, latitude_centre, longitude_centre, rayon_km, nb_antennes)
# =============================================================
ZONES = [
    ("Mahdia Centre",   35.504, 11.020, 0.7,  12),  # Légèrement à l'intérieur des terres
    ("Mahdia Nord",     35.525, 11.010, 0.7,   9),
    ("Mahdia Sud",      35.468, 11.010, 0.7,   8),
    ("Ksour Essef",     35.414, 10.970, 1.0,   9),
    ("El Jem",          35.292, 10.711, 1.2,   9),
    ("Chebba",          35.230, 10.990, 0.7,   8),
    ("Salakta",         35.393, 11.005, 0.7,   8),
    ("Sidi Alouane",    35.367, 10.920, 1.0,   8),
    ("Bou Merdes",      35.438, 10.710, 1.0,   9),  # +1
    ("Melloulèche",     35.176, 10.980, 0.7,   7),
    ("Ouled Chamekh",   35.474, 10.321, 1.0,   8),
    ("Hebira",          35.345, 10.970, 0.8,   9),  # +1
    ("Essouassi",       35.331, 10.543, 1.0,   8),
    ("Chorbane",        35.278, 10.388, 1.0,   8),
]
# Total : 12+9+8+9+9+8+8+8+9+7+8+9+8+8 = 120 ✔

TYPES_ANTENNE = ["4G LTE", "4G+", "5G", "3G", "Macro", "Micro"]


def longitude_max_pour_latitude(lat):
    """
    Empêche de placer des antennes dans la Méditerranée.
    La côte est à l'Est — longitude max dépend de la latitude.
    """
    if lat >= 35.49:
        return 11.038   # Conservatif : 6mm de marge sur la côte
    elif lat >= 35.40:
        return 11.035
    elif lat >= 35.28:
        return 11.035
    elif lat >= 35.14:
        return 11.025
    else:
        return 11.000


def generer_point(lat_centre, lon_centre, rayon_km):
    """
    Génère des coordonnées GPS dans un rayon (en km) autour du centre.
    """
    delta = rayon_km / 111.0  # 1 degré ≈ 111 km

    for _ in range(500):
        lat = lat_centre + random.uniform(-delta, delta)
        lon = lon_centre + random.uniform(-delta, delta)
        lon_max = longitude_max_pour_latitude(lat)
        if lon <= lon_max and 35.10 <= lat <= 35.60 and 10.20 <= lon <= lon_max:
            return round(lat, 6), round(lon, 6)

    # Fallback garanti : coordonnées du centre de la zone avec légère variation
    return round(lat_centre + random.uniform(-0.002, 0.002), 6), \
           round(min(lon_centre, longitude_max_pour_latitude(lat_centre) - 0.005), 6)


def inserer_antennes():
    """
    Connexion PostgreSQL et insertion de 120 antennes fixes.
    """
    print("[DÉMARRAGE] Connexion à la base de données...")
    conn = psycopg2.connect(
        dbname="antennes_mahdia", user="postgres",
        password="1234", host="postgres", port="5432"
    )
    cur = conn.cursor()

    print("[INFO] Suppression des anciennes données...")
    cur.execute("DELETE FROM mesures;")
    cur.execute("DELETE FROM antennes;")

    print("[INFO] Insertion de 120 antennes fixes...")
    ant_id = 1

    for (nom_zone, lat_c, lon_c, rayon, nb) in ZONES:
        for i in range(nb):
            lat, lon = generer_point(lat_c, lon_c, rayon)
            type_ant = TYPES_ANTENNE[(ant_id - 1) % len(TYPES_ANTENNE)]

            cur.execute("""
                INSERT INTO antennes
                    (id, nom, zone, type, latitude, longitude, operateur, statut, date_installation,
                     geom)
                VALUES (%s, %s, %s, %s, %s, %s, %s, 'normal', CURRENT_DATE,
                        ST_SetSRID(ST_MakePoint(%s, %s), 4326))
            """, (
                ant_id,
                f"TT_{ant_id:03d}",
                nom_zone,
                type_ant,
                lat, lon,
                "Tunisie Telecom",
                lon, lat
            ))
            ant_id += 1

    conn.commit()
    cur.close()
    conn.close()

    total = ant_id - 1
    print(f"[OK] {total} antennes insérées dans {len(ZONES)} zones.")
    if total != 120:
        print(f"[AVERTISSEMENT] {total} antennes au lieu de 120 — vérifier les zones.")


if __name__ == "__main__":
    inserer_antennes()
