"""
Simulateur de mesures réseau — Tunisie Telecom NOC
===================================================
Rôle UNIQUE : générer des mesures réseau réalistes toutes les 30 minutes.

AUCUNE logique de classification (normal/alerte/critique) ici.
La classification est entièrement déléguée au moteur IA (Isolation Forest)
dans l'API Flask après chaque cycle de simulation.
"""
import os
import time
import random
from datetime import datetime
import psycopg2
import schedule

# ── Configuration ───────────────────────────────────────────────────────────
INTERVALLE_SECONDES = 1800   # 30 minutes — une mesure par antenne par cycle
API_PREDICT_URL     = "http://api:5000/internal/predict"

# ── Connexion DB ─────────────────────────────────────────────────────────────
def connecter():
    url = os.getenv("DATABASE_URL", "postgresql://postgres:1234@postgres:5432/antennes_mahdia")
    for _ in range(20):
        try:
            return psycopg2.connect(url)
        except Exception:
            time.sleep(3)
    raise RuntimeError("Impossible de se connecter à PostgreSQL après 20 tentatives.")


# ── Génération de mesures brutes ─────────────────────────────────────────────
def generer_mesures(ant_type, prev=None):
    """
    Génère des métriques réseau réalistes basées sur une dérive lente depuis
    l'état précédent (ou un état initial sain). 
    NE CALCULE AUCUN STATUT — le statut est déterminé par l'IA.
    """
    if not prev:
        # État initial — réseau sain
        cpu      = random.uniform(20, 50)
        temp     = 35 + (cpu * 0.3)
        ram      = 30 + (cpu * 0.2)
        dispo    = random.uniform(97.0, 100.0)
        latence  = random.uniform(10, 25)
        pkt_loss = random.uniform(0.05, 0.5)
        jitter   = random.uniform(2, 8)
        debit    = random.uniform(150, 300) if ant_type == '5G' else random.uniform(60, 150)
    else:
        # Dérive lente — simule l'évolution naturelle du réseau
        # La disponibilité peut descendre significativement si le site se dégrade
        cpu      = max(5.0,   min(99.0,  prev['cpu']      + random.uniform(-5, 8)))
        temp     = max(30.0,  min(95.0,  prev['temp']     + random.uniform(-2, 4)))
        ram      = max(10.0,  min(99.0,  prev['ram']      + random.uniform(-3, 5)))
        # Dérive asymétrique : la dispo peut chuter rapidement mais remonte lentement
        dispo    = max(82.0,  min(100.0, prev['dispo']    + random.uniform(-2.5, 0.8)))
        latence  = max(5.0,   min(200.0, prev['latence']  + random.uniform(-10, 12)))
        pkt_loss = max(0.0,   min(20.0,  prev['pkt_loss'] + random.uniform(-0.3, 0.6)))
        jitter   = max(1.0,   min(40.0,  prev.get('jitter', 5.0) + random.uniform(-2, 3)))
        if ant_type == '5G':
            debit = max(30.0, min(400.0, prev['debit'] + random.uniform(-30, 25)))
        else:
            debit = max(10.0, min(220.0, prev['debit'] + random.uniform(-25, 20)))

        # ── Simulation d'incidents réalistes ──────────────────────────────────
        # 5% de chance qu'un site entre en mode dégradé (surcharge CPU / surchauffe)
        if random.random() < 0.05:
            cpu     = random.uniform(78, 99)
            temp    = random.uniform(70, 92)
            ram     = random.uniform(75, 99)
            latence = random.uniform(80, 200)
            dispo   = random.uniform(82, 93)
            pkt_loss = random.uniform(3, 15)

    # Signal RSSI (dBm) — indépendant du cycle
    signal = random.uniform(-92, -48)

    return {
        "temperature": round(temp, 1),
        "cpu":         round(cpu, 1),
        "ram":         round(ram, 1),
        "debit":       round(debit, 1),
        "latence":     round(latence, 1),
        "packet_loss": round(pkt_loss, 2),
        "signal":      round(signal, 1),
        "disponibilite": round(dispo, 1),
        "jitter":      round(jitter, 1),
    }



# ── Job principal ────────────────────────────────────────────────────────────
def job_simulation():
    """
    Cycle de simulation toutes les 30 minutes :
      1. Récupère les dernières mesures de chaque antenne (pour la dérive)
      2. Génère de nouvelles mesures brutes
      3. Insère dans la table 'mesures' avec statut = 'analyse_ia_en_cours'
      4. Déclenche l'analyse IA via /internal/predict pour classifier les sites
    """
    conn = connecter()
    cur  = conn.cursor()

    # Récupère l'état précédent depuis la vue antennes_statut
    cur.execute("""
        SELECT a.id, a.type,
               s.temperature, s.cpu, s.ram, s.traffic,
               s.latence, s.disponibilite, s.packet_loss, s.jitter
        FROM antennes a
        LEFT JOIN antennes_statut s ON a.id = s.id
    """)
    antennes = cur.fetchall()

    now   = datetime.now()
    count = 0

    for row in antennes:
        ant_id, ant_type, p_temp, p_cpu, p_ram, p_debit, p_lat, p_dispo, p_pkt, p_jit = row

        prev = None
        if p_temp is not None:
            prev = {
                'temp':     float(p_temp),
                'cpu':      float(p_cpu),
                'ram':      float(p_ram),
                'debit':    float(p_debit or 0),
                'latence':  float(p_lat  or 0),
                'dispo':    float(p_dispo or 100),
                'pkt_loss': float(p_pkt  or 0),
                'jitter':   float(p_jit  or 0),
            }

        m = generer_mesures(ant_type, prev)

        # Insertion : statut = 'analyse_ia_en_cours' — sera mis à jour par l'IA
        cur.execute("""
            INSERT INTO mesures
                (antenne_id, temperature, cpu, ram, traffic, latence,
                 packet_loss, signal, disponibilite, jitter, statut, date_mesure)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            ant_id,
            m["temperature"], m["cpu"], m["ram"], m["debit"], m["latence"],
            m["packet_loss"], m["signal"], m["disponibilite"], m["jitter"],
            "analyse_ia_en_cours",
            now
        ))
        count += 1

    conn.commit()
    cur.close()
    conn.close()
    print("[SIMULATION] Nouvelle mesure générée")

    # Déclenche l'analyse Isolation Forest (classification centralisée)
    try:
        import requests
        res = requests.get(API_PREDICT_URL, timeout=60)
        print("[IA] Analyse déclenchée")
        print("[SYNC] Dashboard mis à jour")
    except Exception as e:
        print(f"[IA TRIGGER ERROR] {e}")


def attendre_api(max_tentatives=30, delai=5):
    """
    Attend que l'API Flask soit disponible avant de déclencher la première simulation.
    Rétente toutes les `delai` secondes jusqu'à `max_tentatives`.
    """
    import requests
    for i in range(1, max_tentatives + 1):
        try:
            requests.get("http://api:5000/", timeout=3)
            print(f"[INIT] API disponible après {i} tentative(s).")
            return True
        except Exception:
            print(f"[INIT] API non disponible ({i}/{max_tentatives}), nouvel essai dans {delai}s...")
            time.sleep(delai)
    print("[INIT] API toujours inaccessible — simulation continue sans IA au démarrage.")
    return False


# ── Démarrage ────────────────────────────────────────────────────────────────
def demarrer():
    print("[INIT] Simulateur NOC démarré — intervalle: 30 min")

    # Attendre que l'API Flask soit prête avant le premier cycle de simulation
    attendre_api()
    
    # Exécution immédiate au démarrage
    job_simulation()
    
    # Planification toutes les 30 minutes
    schedule.every(30).minutes.do(job_simulation)

    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        print("[STOP] Simulateur arrêté proprement.")


if __name__ == "__main__":
    demarrer()