"""
simulation/generate_mesures.py — Simulateur de mesures réseau
======================================================
Tunisie Telecom NOC — Mahdia

Rôle : Générer des mesures réseau réalistes toutes les 2 minutes
       et déclencher le moteur IA (Isolation Forest) après chaque cycle.

Architecture :
  1. Ce script génère des mesures BRUTES sans statut.
  2. L'IA Flask (Isolation Forest) détermine ensuite le statut.
  3. La vue antennes_statut est mise à jour automatiquement.
"""
import os
import time
import random
from datetime import datetime
import psycopg2
import schedule

# ── Configuration ─────────────────────────────────────────────────────────────
INTERVALLE_MINUTES  = 10       # Cycle de simulation (10 minutes)
API_PREDICT_URL     = "http://api:5000/internal/predict"

# ── Connexion DB ──────────────────────────────────────────────────────────────
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


# ── Génération de mesures brutes ──────────────────────────────────────────────
def generer_mesures(ant_type: str, prev: dict = None) -> dict:
    """
    Génère des métriques réseau réalistes avec dérive progressive depuis l'état précédent.
    Plages : 
      - température : 15 - 95
      - cpu : 0 - 100
      - ram : 0 - 100
      - traffic : 0 - 1500
      - latence : 0 - 500
      - packet_loss : 0 - 25
      - signal : -120 - -40
      - disponibilite : 40 - 100
      - jitter : 0 - 200
    """
    if not prev:
        # État initial — réseau sain
        cpu      = random.uniform(10, 40)
        temp     = 25 + (cpu * 0.2)
        ram      = 20 + (cpu * 0.3)
        dispo    = random.uniform(98.0, 100.0)
        latence  = random.uniform(5, 20)
        pkt_loss = random.uniform(0.0, 0.2)
        jitter   = random.uniform(1, 5)
        debit    = random.uniform(500, 1000) if ant_type == '5G' else random.uniform(100, 400)
        signal   = random.uniform(-70, -50)
    else:
        # Dérive lente — simule l'évolution naturelle du réseau
        cpu      = max(0.0,   min(100.0, prev['cpu']      + random.uniform(-5, 8)))
        temp     = max(15.0,  min(95.0,  prev['temp']     + random.uniform(-2, 3)))
        ram      = max(0.0,   min(100.0, prev['ram']      + random.uniform(-3, 4)))
        dispo    = max(40.0,  min(100.0, prev['dispo']    + random.uniform(-1, 0.5)))
        latence  = max(0.0,   min(500.0, prev['latence']  + random.uniform(-5, 10)))
        pkt_loss = max(0.0,   min(25.0,  prev['pkt_loss'] + random.uniform(-0.1, 0.3)))
        jitter   = max(0.0,   min(200.0, prev.get('jitter', 5.0) + random.uniform(-2, 3)))
        
        # Le trafic varie plus fortement
        variation_debit = random.uniform(-50, 60) if ant_type == '5G' else random.uniform(-30, 40)
        debit = max(0.0, min(1500.0, prev['debit'] + variation_debit))

        # Le signal fluctue légèrement
        signal = max(-120.0, min(-40.0, prev.get('signal', -60.0) + random.uniform(-3, 3)))

        # ── Simulation d'anomalies / dégradations réalistes ──────
        rand_incident = random.random()
        if rand_incident < 0.05:
            # 5% de chances : Dégradation modérée (Alerte)
            cpu      = min(100.0, cpu + random.uniform(20, 40))
            latence  = min(500.0, latence + random.uniform(50, 150))
            dispo    = max(40.0, dispo - random.uniform(2, 10))
            pkt_loss = min(25.0, pkt_loss + random.uniform(2, 5))
            jitter   = min(200.0, jitter + random.uniform(10, 30))
        elif rand_incident < 0.07:
            # 2% de chances : Anomalie critique (Critique)
            cpu      = random.uniform(85, 100)
            temp     = random.uniform(80, 95)
            ram      = random.uniform(85, 100)
            latence  = random.uniform(200, 500)
            dispo    = random.uniform(40, 80)
            pkt_loss = random.uniform(10, 25)
            jitter   = random.uniform(100, 200)
            signal   = random.uniform(-120, -100)

    return {
        "temperature":  round(temp, 1),
        "cpu":          round(cpu, 1),
        "ram":          round(ram, 1),
        "debit":        round(debit, 1),
        "latence":      round(latence, 1),
        "packet_loss":  round(pkt_loss, 2),
        "signal":       round(signal, 1),
        "disponibilite": round(dispo, 1),
        "jitter":       round(jitter, 1),
    }


# ── Job principal ─────────────────────────────────────────────────────────────
def job_simulation():
    """
    Cycle de simulation complet :
      1. Récupère l'état précédent de chaque antenne (dérive progressive)
      2. Génère de nouvelles mesures brutes
      3. Insère en base avec statut = 'analyse_ia_en_cours'
      4. Déclenche l'Isolation Forest via /internal/predict
    """
    print(f"[SIM] Début du cycle — {datetime.now().strftime('%H:%M:%S')}")
    try:
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
                    'latence':  float(p_lat   or 0),
                    'dispo':    float(p_dispo  or 100),
                    'pkt_loss': float(p_pkt   or 0),
                    'jitter':   float(p_jit   or 0),
                }

            m = generer_mesures(ant_type, prev)
            cur.execute("""
                INSERT INTO mesures
                    (antenne_id, temperature, cpu, ram, traffic, latence,
                     packet_loss, signal, disponibilite, jitter, statut, date_mesure)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                ant_id,
                m["temperature"], m["cpu"],  m["ram"],   m["debit"],  m["latence"],
                m["packet_loss"], m["signal"], m["disponibilite"], m["jitter"],
                "analyse_ia_en_cours", now
            ))
            count += 1

        conn.commit()
        cur.close(); conn.close()
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


# ── Attente de disponibilité de l'API ────────────────────────────────────────
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


# ── Démarrage ─────────────────────────────────────────────────────────────────
def demarrer():
    print(f"[INIT] Simulateur NOC démarré — intervalle: {INTERVALLE_MINUTES} min")
    attendre_api()

    # Premier cycle immédiat au démarrage
    job_simulation()

    # Planification régulière
    schedule.every(INTERVALLE_MINUTES).minutes.do(job_simulation)

    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        print("[STOP] Simulateur arrêté proprement.")


if __name__ == "__main__":
    demarrer()