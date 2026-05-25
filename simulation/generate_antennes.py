"""
generate_antennes.py  —  Script de peuplement initial
Plateforme NOC Tunisie Télécom — Gouvernorat de Mahdia

Génère exactement 120 antennes simulées + 1 antenne IoT réelle (ISET Mahdia).
Toutes les antennes démarrent avec des mesures normales :
  Température ≈ 28°C, CPU ≈ 40%, Signal ≈ -65 dBm, Latence ≈ 15ms, Dispo ≈ 99%

L'Isolation Forest apprend ces valeurs comme comportement normal
et détecte les écarts sans aucune règle codée en dur.
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

# Antenne IoT réelle — Arduino Uno + DHT11
ISET_MAHDIA = {
    "nom":       "ISET Mahdia",
    "zone":      "Mahdia Nord",   # zone géographiquement proche
    "type":      "4G",
    "latitude":  35.522473,
    "longitude": 11.030388,
    "operateur": "Tunisie Telecom",
}

# Mesure initiale pour ISET Mahdia (comportement normal de la zone)
# La température réelle viendra du capteur DHT11 via serial_bridge.py
ISET_MAHDIA_MESURE = {
    "temperature":   28.0,    # valeur de démarrage — écrasée par le DHT11
    "cpu":           38.0,    # simulé (profil Mahdia Nord)
    "signal":        -61.0,   # simulé (bon signal en zone Nord)
    "latence":       12.0,    # simulé (faible latence)
    "disponibilite": 99.5,    # simulé
}


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
    Connexion PostgreSQL et insertion de 120 antennes simulées + ISET Mahdia.
    Toutes les antennes ont des mesures initiales normales.
    """
    print("[DÉMARRAGE] Connexion à la base de données...")
    conn = psycopg2.connect(
        dbname="antennes_mahdia", user="postgres",
        password="1234", host="postgres", port="5432"
    )
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM antennes")
    nb_existantes = cur.fetchone()[0]
    if nb_existantes > 0:
        print(f"[INFO] {nb_existantes} antennes déjà en base — historique des mesures conservé.")
        cur.close()
        conn.close()
        return

    # Initialisation uniquement si la base est vide (jamais de DELETE sur mesures)
    if nb_existantes > 0:
        print(f"[INFO] {nb_existantes} antenne(s) présentes — ajout sans effacer l'historique.")
    else:
        print("[INFO] Base vide — insertion initiale des 121 antennes.")

    print("[INFO] Insertion de 120 antennes simulées...")
    ant_id = 1

    for (nom_zone, lat_c, lon_c, rayon, nb) in ZONES:
        for i in range(nb):
            lat, lon = generer_point(lat_c, lon_c, rayon)
            type_ant = TYPES_ANTENNE[(ant_id - 1) % len(TYPES_ANTENNE)]

            # Valeurs de base centrées autour des cibles normales
            base_cpu     = 30 + (ant_id % 20)          # 30–50%
            base_temp    = 24 + (ant_id % 8) + (base_cpu * 0.02)  # 24–32°C
            base_latence = 10 + (ant_id % 12)          # 10–22 ms
            base_dispo   = 98.5 + ((ant_id % 10) / 20.0)  # 98.5–99.5%
            signal_dbm   = -75 + (ant_id % 20)         # -75 à -55 dBm

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

            # Insérer 6 mesures initiales normales pour chaque antenne
            for k in range(1, 7):
                cur.execute("""
                    INSERT INTO mesures
                        (antenne_id, temperature, cpu, signal, latence, disponibilite,
                         statut, risk_score, date_mesure)
                    VALUES (%s, %s, %s, %s, %s, %s, 'normal', 85.0,
                            NOW() - (%s * INTERVAL '30 minutes'))
                """, (
                    ant_id,
                    round(min(45.0, max(15.0, base_temp    + (k - 4) * 0.2)), 2),
                    round(max(10.0, min(80.0, base_cpu     + (k - 4) * 0.5)), 2),
                    round(signal_dbm + (k % 3) * 0.3,                         2),
                    round(max(5.0,            base_latence + (k - 4) * 0.4),  2),
                    round(min(100.0, max(97.0, base_dispo  - (k % 2) * 0.03)), 2),
                    6 - k,
                ))

            ant_id += 1

    # ── Insertion de l'antenne IoT réelle : ISET Mahdia ──
    print("[INFO] Insertion de l'antenne IoT réelle : ISET Mahdia (ID=121)...")
    lat_iset = ISET_MAHDIA["latitude"]
    lon_iset = ISET_MAHDIA["longitude"]
    cur.execute("""
        INSERT INTO antennes
            (id, nom, zone, type, latitude, longitude, operateur, statut, date_installation, geom)
        VALUES (121, %s, %s, %s, %s, %s, %s, 'normal', CURRENT_DATE,
                ST_SetSRID(ST_MakePoint(%s, %s), 4326))
        ON CONFLICT (id) DO NOTHING
    """, (
        ISET_MAHDIA["nom"], ISET_MAHDIA["zone"], ISET_MAHDIA["type"],
        lat_iset, lon_iset, ISET_MAHDIA["operateur"],
        lon_iset, lat_iset
    ))

    # Mesure initiale normale pour ISET Mahdia
    # (la température réelle du DHT11 prendra le relais via serial_bridge.py)
    cur.execute("""
        INSERT INTO mesures
            (antenne_id, temperature, cpu, signal, latence, disponibilite,
             statut, risk_score, date_mesure)
        VALUES (121, %s, %s, %s, %s, %s, 'normal', 85.0, NOW())
    """, (
        ISET_MAHDIA_MESURE["temperature"],
        ISET_MAHDIA_MESURE["cpu"],
        ISET_MAHDIA_MESURE["signal"],
        ISET_MAHDIA_MESURE["latence"],
        ISET_MAHDIA_MESURE["disponibilite"],
    ))

    conn.commit()
    cur.close()
    conn.close()

    total = ant_id - 1
    print(f"[OK] {total} antennes simulées + 1 antenne IoT (ISET Mahdia) insérées.")
    print(f"[OK] Toutes les antennes démarrent en état NORMAL.")
    print(f"[OK] Profil de démarrage : Temp≈{ISET_MAHDIA_MESURE['temperature']}°C | "
          f"CPU≈{ISET_MAHDIA_MESURE['cpu']}% | Signal≈{ISET_MAHDIA_MESURE['signal']}dBm | "
          f"Latence≈{ISET_MAHDIA_MESURE['latence']}ms | Dispo≈{ISET_MAHDIA_MESURE['disponibilite']}%")
    if total != 120:
        print(f"[AVERTISSEMENT] {total} antennes simulées au lieu de 120 — vérifier les zones.")


if __name__ == "__main__":
    inserer_antennes()
