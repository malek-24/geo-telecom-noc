"""
simulation/generate_mesures.py — Simulateur de mesures réseau
======================================================
Tunisie Telecom NOC — Mahdia
Métriques : temperature, cpu, signal, latence, disponibilite
"""
import os
import time
import random
from datetime import datetime
import psycopg2
import schedule

INTERVALLE_MINUTES = 10
API_PREDICT_URL    = "http://api:5000/internal/predict"


def connecter():
    """Connexion PostgreSQL avec retry automatique (20 tentatives × 3s)."""
    url = os.getenv("DATABASE_URL", "postgresql://postgres:1234@postgres:5432/antennes_mahdia")
    for attempt in range(1, 21):
        try:
            return psycopg2.connect(url)
        except Exception as e:
            print(f"[DB] Tentative {attempt}/20 — {e}")
            time.sleep(3)
    raise RuntimeError("Impossible de se connecter à PostgreSQL après 20 tentatives.")


def generer_mesures(ant_type: str, prev: dict = None) -> dict:
    """
    Génère des métriques réseau réalistes avec dérive progressive.
    Métriques : temperature, cpu, signal, latence, disponibilite
    """
    if not prev:
        # État initial — réseau sain
        cpu     = random.uniform(10, 40)
        temp    = 25 + (cpu * 0.2)
        dispo   = random.uniform(98.0, 100.0)
        latence = random.uniform(5, 20)
        signal  = random.uniform(-70, -50)
    else:
        # Dérive lente depuis l'état précédent
        cpu     = max(0.0,   min(100.0, prev['cpu']     + random.uniform(-5, 8)))
        temp    = max(15.0,  min(95.0,  prev['temp']    + random.uniform(-2, 3)))
        dispo   = max(40.0,  min(100.0, prev['dispo']   + random.uniform(-1, 0.5)))
        latence = max(0.0,   min(500.0, prev['latence'] + random.uniform(-5, 10)))
        signal  = max(-120.0, min(-40.0, prev.get('signal', -60.0) + random.uniform(-3, 3)))

        # Simulation d'anomalies / dégradations
        rand = random.random()
        if rand < 0.05:
            # 5% : Dégradation modérée (Alerte)
            cpu     = min(100.0, cpu + random.uniform(20, 40))
            latence = min(500.0, latence + random.uniform(50, 150))
            dispo   = max(40.0,  dispo - random.uniform(2, 10))
            signal  = max(-120.0, signal - random.uniform(10, 25))
        elif rand < 0.07:
            # 2% : Anomalie critique
            cpu     = random.uniform(85, 100)
            temp    = random.uniform(80, 95)
            latence = random.uniform(200, 500)
            dispo   = random.uniform(40, 80)
            signal  = random.uniform(-120, -100)

    return {
        "temperature":  round(temp, 1),
        "cpu":          round(cpu, 1),
        "signal":       round(signal, 1),
        "latence":      round(latence, 1),
        "disponibilite": round(dispo, 1),
    }


def job_simulation():
    """
    Cycle de simulation complet :
      1. Récupère l'état précédent (dérive progressive)
      2. Génère de nouvelles mesures brutes
      3. Insère en base
      4. Déclenche l'Isolation Forest
    """
    print(f"[SIM] Début du cycle — {datetime.now().strftime('%H:%M:%S')}")
    try:
        conn = connecter()
        cur  = conn.cursor()

        cur.execute("""
            SELECT a.id, a.type,
                   s.temperature, s.cpu, s.signal, s.latence, s.disponibilite
            FROM antennes a
            LEFT JOIN antennes_statut s ON a.id = s.id
        """)
        antennes = cur.fetchall()
        now      = datetime.now()
        count    = 0

        for row in antennes:
            ant_id, ant_type, p_temp, p_cpu, p_signal, p_lat, p_dispo = row
            prev = None
            if p_temp is not None:
                prev = {
                    'temp':     float(p_temp),
                    'cpu':      float(p_cpu),
                    'signal':   float(p_signal or -60),
                    'latence':  float(p_lat   or 0),
                    'dispo':    float(p_dispo  or 100),
                }

            m = generer_mesures(ant_type, prev)
            cur.execute("""
                INSERT INTO mesures (antenne_id, temperature, cpu, signal, latence, disponibilite, statut, date_mesure)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                ant_id,
                m["temperature"], m["cpu"], m["signal"],
                m["latence"], m["disponibilite"],
                "analyse_ia_en_cours", now
            ))
            count += 1

        conn.commit()
        cur.close()
        conn.close()
        print(f"[SIM] {count} mesures insérées.")

    except Exception as e:
        print(f"[SIM ERREUR] {e}")
        return

    # Déclenche le moteur Isolation Forest
    try:
        import requests
        res = requests.get(API_PREDICT_URL, timeout=60)
        print(f"[IA] Analyse déclenchée — HTTP {res.status_code}")
    except Exception as e:
        print(f"[IA ERREUR] {e}")


def attendre_api(max_tentatives: int = 30, delai: int = 5) -> bool:
    """Attend que l'API Flask soit disponible avant le premier cycle."""
    import requests
    for i in range(1, max_tentatives + 1):
        try:
            r = requests.get("http://api:5000/health", timeout=3)
            if r.status_code == 200:
                print(f"[INIT] API disponible après {i} tentative(s).")
                return True
        except Exception:
            pass
        print(f"[INIT] API non disponible ({i}/{max_tentatives}), nouvel essai dans {delai}s…")
        time.sleep(delai)
    print("[INIT] API toujours inaccessible — simulation continue sans IA au démarrage.")
    return False


def demarrer():
    print(f"[INIT] Simulateur NOC démarré — intervalle: {INTERVALLE_MINUTES} min")
    attendre_api()
    job_simulation()
    schedule.every(INTERVALLE_MINUTES).minutes.do(job_simulation)
    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        print("[STOP] Simulateur arrêté proprement.")


if __name__ == "__main__":
    demarrer()