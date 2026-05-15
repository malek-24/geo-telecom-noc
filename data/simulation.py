import os
import csv
import math
import random
import psycopg2

random.seed(42)

# ------------------------------------------------------------------
# ZONES (محسّنة)
# ------------------------------------------------------------------
ZONES = [
    ('Mahdia_Ville',     35.504, 11.055, 2.0, 6),
    ('Rejiche',          35.471, 11.041, 1.5, 5),
    ('ksour essef',      35.414, 10.98,  1.5, 5),
    ('salakta',          35.393, 11.027,  1.5, 5),
    ('sidi alouane',     35.367, 10.931,  1.5, 4),
    ('eljam',            35.292, 10.711,  1.5, 5),
    ('gouessem',         35.214, 10.463,  1.5, 3),
    ('menzel hachad',    35.186, 10.287, 1.5, 3),
    ('chorbane',         35.278, 10.388, 1.5, 4),
    ('essouassi',        35.331, 10.543, 1.5, 4),
    ('ouled chamekh',    35.474, 10.321, 1.5, 3),
    ('boumerdes',        35.438, 10.721, 1.5, 4),
    ('ouled salah',      35.422, 10.912, 1.5, 3),
    ('zorda',            35.296, 10.923,1.5, 3),
    ('melloulech',       35.176, 11.027, 1.5, 3),
    ('ghedhabna',        35.288, 11.052,1.5, 3),
    ('zalba est',        35.240, 10.885, 1.5, 3),
    ('oued beja nord',   35.363, 10.886, 1.5, 3),
    ('ouedglet',         35.361, 10.827, 1.5, 3),
    ('riadh bou helal',  35.269, 10.600, 1.5, 3),
    ('sidi naceur',      35.319, 10.609, 1.5, 3),
    ('sidi zaid',        35.366, 10.500, 1.5, 3),
    ('el kesasba',       35.376, 10.633,1.5, 3),
    ('bouhlale',         35.442, 10.621, 1.5, 3),
    ('bouhlale ali nord',35.424, 10.652,1.5, 3),
    ('kerker',           35.474, 10.647, 1.5, 3),
    ('kerker 2',         35.461, 10.663, 1.5, 3),
    ('azarata',          35.430, 10.686, 1.5, 3),
    ('alrawadi',         35.406, 10.703, 1.5, 3),
    ('al chawaria',      35.430, 10.767, 1.5, 3),
    ('al ababsa',        35.387, 10.770, 1.5, 3),
    ('sidi assaker',     35.408, 10.892, 1.5, 3),
    ('jouaouda',         35.476, 10.880, 1.5, 3),
    ('es saad',          35.481, 10.938, 1.5, 3),
    ('chiba',            35.519, 10.940, 1.5, 3),
    ('el bradaa',        35.345, 10.987, 1.5, 3),
]

# ------------------------------------------------------------------
# Génération coordonnée réaliste
# ------------------------------------------------------------------
def generer_coordonnees(lat_c, lon_c, rayon_km):
    r = rayon_km / 111.0

    angle = random.uniform(0, 2 * math.pi)
    dist = r * math.sqrt(random.uniform(0.2, 1))  # 🔥 ما يخليش كلهم في الوسط

    lat = lat_c + dist * math.cos(angle)
    lon = lon_c + dist * math.sin(angle)

    # ❌ منع البحر (مهم)
    coast_limit = 11.06 + (lat - 35.50) * 0.05
    if lon > coast_limit:
        lon = coast_limit - random.uniform(0.005, 0.02)

    return round(lat, 6), round(lon, 6)

# ------------------------------------------------------------------
# Génération antennes
# ------------------------------------------------------------------
def generer_antennes():
    antennes = []
    idx = 1

    for zone, lat_c, lon_c, rayon_km, nb in ZONES:
        for _ in range(nb):
            lat, lon = generer_coordonnees(lat_c, lon_c, rayon_km)

            antennes.append({
                "id": idx,
                "nom": f"TT_Antenne_{idx:03d}",
                "zone": zone,
                "type": random.choice(["fixe", "mobile"]),
                "latitude": lat,
                "longitude": lon,
                "temperature": round(random.uniform(25, 85), 2),
                "cpu": round(random.uniform(30, 95), 2),
            })
            idx += 1

    return antennes

# ------------------------------------------------------------------
# CSV
# ------------------------------------------------------------------
def exporter_csv(antennes):
    os.makedirs("data", exist_ok=True)

    with open("data/antennes.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id","nom","zone","type","latitude","longitude","temperature","cpu"])

        for a in antennes:
            writer.writerow([
                a["id"], a["nom"], a["zone"], a["type"],
                a["latitude"], a["longitude"],
                a["temperature"], a["cpu"]
            ])

    print("✅ CSV généré")

# ------------------------------------------------------------------
# DB UPDATE (FIXED 🔥)
# ------------------------------------------------------------------
def update_db(antennes):
    conn = psycopg2.connect(
        dbname="antennes_mahdia",
        user="postgres",
        password="1234",
        host="localhost",
        port="5432"
    )

    cur = conn.cursor()

    # 🧹 تنظيف
    cur.execute("DELETE FROM mesures;")
    cur.execute("DELETE FROM antennes;")

    for a in antennes:

        # ✅ INSERT antenne
        cur.execute("""
            INSERT INTO antennes (id, nom, zone, type, latitude, longitude, operateur, geom)
            VALUES (%s, %s, %s, %s, %s, %s, %s,
                    ST_SetSRID(ST_MakePoint(%s, %s), 4326))
        """, (
            a["id"], a["nom"], a["zone"], a["type"],
            a["latitude"], a["longitude"],
            "Tunisie Telecom",
            a["longitude"], a["latitude"]
        ))

        # ✅ INSERT mesure
        cur.execute("""
            INSERT INTO mesures (antenne_id, temperature, cpu)
            VALUES (%s, %s, %s)
        """, (a["id"], a["temperature"], a["cpu"]))

    conn.commit()
    conn.close()

    print("✅ DB RESET + INSERT OK")

# ------------------------------------------------------------------
# MAIN
# ------------------------------------------------------------------
if __name__ == "__main__":
    print("🔄 génération...")

    antennes = generer_antennes()

    exporter_csv(antennes)
    update_db(antennes)

    print("✅ FINISHED (positions réalistes Mahdia)")