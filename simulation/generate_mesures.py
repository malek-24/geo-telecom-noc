"""
simulation/generate_mesures.py — Simulateur Mean-Reverting Random Walk
=======================================================================
GEO-TÉLÉCOM NOC — Mahdia
PFE Licence — Réseaux & Télécommunications 2025/2026

PRINCIPE — Mean-Reverting Random Walk (MRRW) :
  Chaque métrique évolue progressivement vers une valeur cible,
  avec un bruit léger. Le résultat : un réseau "vivant" qui ne
  reste jamais complètement statique, mais sans sauts brutaux.

FORMULE :
  val_nouvelle = val_précédente + alpha × (cible - val_précédente) + bruit
  avec :
    alpha = 0.15  (vitesse de retour vers la cible)
    bruit = gauss(0, bruit_std)  (variation naturelle légère)

EXEMPLES de séquences naturelles :
  Température : 28.0 → 28.2 → 27.9 → 28.4 → 28.1
  CPU         : 40.0 → 41.0 → 39.0 → 42.0 → 40.0
  Signal      : -65  → -64  → -66  → -65  → -63

VALEURS CIBLES (comportement réseau sain) :
  Température   : 28°C
  CPU           : 40%
  Signal RSSI   : -65 dBm
  Latence       : 15 ms
  Disponibilité : 99%

ANTENNE ISET MAHDIA :
  Exclue de ce simulateur. Sa température réelle vient du capteur
  DHT11 via Arduino → serial_bridge.py → /iot/mesure.

RÈGLE IMPORTANTE — AUCUNE ANOMALIE ALÉATOIRE :
  Ce simulateur ne génère jamais d'anomalie automatiquement.
  Le réseau démarre et reste en état NORMAL.
  Les anomalies proviennent UNIQUEMENT :
    1. D'une modification manuelle de l'admin (PUT /antennes/{id}/metriques)
    2. Du capteur DHT11 chauffé (ISET Mahdia via /iot/mesure)
    3. D'un test IA volontaire (POST /api/test-ia)
"""

import os
import time
import random
from datetime import datetime
import psycopg2
import schedule


# ── CONFIGURATION ─────────────────────────────────────────────────
INTERVALLE_SECONDES = 3         # Cycle global : toutes les 3 secondes (soutenance)
ISET_MAHDIA_NOM     = "ISET Mahdia"   # Exclue — données DHT11 via serial_bridge.py
API_IA_URL          = "http://api:5000/internal/predict"

# ── PARAMÈTRES MRRW ───────────────────────────────────────────────
# Mean-Reverting Random Walk : val = prev + alpha × (cible - prev) + bruit
ALPHA = 0.15   # Vitesse de retour vers la cible (0 = immobile, 1 = saut direct)

# Valeurs cibles — comportement normal du réseau
CIBLES = {
    "temp":    28.0,    # °C
    "cpu":     40.0,    # %
    "signal":  -65.0,   # dBm
    "latence": 15.0,    # ms
    "dispo":   99.0,    # %
}

# Bruit gaussien léger pour un aspect naturel (std)
BRUIT_STD = {
    "temp":    0.10,
    "cpu":     0.30,
    "signal":  0.15,
    "latence": 0.10,
    "dispo":   0.01,
}

# Limites de variation autour de la cible (clip physique)
# Température : ±10% de 28°C → [25.2 , 30.8]
# CPU         : ±10% de 40%  → [36.0 , 44.0]
# Signal      : ±6 dBm       → [-71.0, -59.0]
# Latence     : ±10% de 15ms → [13.5 , 16.5]
# Disponibilité: ±2%         → [97.0 , 100.0]
BORNES = {
    "temp":    (25.0,   32.0),
    "cpu":     (36.0,   44.0),
    "signal":  (-71.0, -59.0),
    "latence": (13.5,   16.5),
    "dispo":   (97.0,  100.0),
}


def connecter():
    """Connexion PostgreSQL avec retry automatique (20 tentatives × 3s)."""
    url = os.getenv("DATABASE_URL", "postgresql://postgres:1234@postgres:5432/antennes_mahdia")
    for tentative in range(1, 21):
        try:
            return psycopg2.connect(url)
        except Exception as e:
            print(f"[DB] Tentative {tentative}/20 — {e}")
            time.sleep(3)
    raise RuntimeError("Impossible de se connecter à PostgreSQL après 20 tentatives.")


def mrrw(prev: float, cle: str) -> float:
    """
    Applique le Mean-Reverting Random Walk pour une métrique.

    Formule : val = prev + alpha × (cible - prev) + bruit
      - Si prev est loin de la cible → alpha ramène vers la cible (15% par cycle)
      - bruit gaussien léger pour un aspect naturel

    Paramètres :
      prev : valeur précédente de la métrique
      cle  : clé dans les dicts CIBLES/BRUIT_STD/BORNES ("temp", "cpu", etc.)

    Retour :
      Nouvelle valeur, clippée dans les bornes physiques.
    """
    cible  = CIBLES[cle]
    bruit  = random.gauss(0, BRUIT_STD[cle])
    val    = prev + ALPHA * (cible - prev) + bruit
    # Clipper dans les bornes physiques
    b_min, b_max = BORNES[cle]
    return round(max(b_min, min(b_max, val)), 2)


def generer_mesures_normales(prev: dict) -> dict:
    """
    Génère des métriques normales via MRRW.

    Paramètre :
      prev : dict avec les valeurs précédentes
             {"temp": 28.0, "cpu": 40.0, "signal": -65.0, "latence": 15.0, "dispo": 99.0}
             Si None → démarre directement sur les valeurs cibles + bruit minimal

    Retour :
      dict {"temperature", "cpu", "signal", "latence", "disponibilite"}
    """
    if prev is None:
        # Première mesure : partir des cibles avec un bruit très léger
        return {
            "temperature":   round(CIBLES["temp"]   + random.gauss(0, 0.1), 2),
            "cpu":           round(CIBLES["cpu"]    + random.gauss(0, 0.3), 2),
            "signal":        round(CIBLES["signal"] + random.gauss(0, 0.2), 2),
            "latence":       round(CIBLES["latence"]+ random.gauss(0, 0.1), 2),
            "disponibilite": round(CIBLES["dispo"]  + random.gauss(0, 0.01), 2),
        }

    # MRRW : évolution progressive depuis la mesure précédente
    return {
        "temperature":   mrrw(prev["temp"],    "temp"),
        "cpu":           mrrw(prev["cpu"],     "cpu"),
        "signal":        mrrw(prev["signal"],  "signal"),
        "latence":       mrrw(prev["latence"], "latence"),
        "disponibilite": mrrw(prev["dispo"],   "dispo"),
    }


def generer_mesures(ant_id: int, prev: dict = None) -> dict:
    """
    Génère les mesures NORMALES pour une antenne via le MRRW.

    RÈGLE : ce simulateur ne génère AUCUNE anomalie aléatoire.
    Toutes les valeurs restent dans les bornes normales définies.
    Les anomalies proviennent uniquement de l'admin, du DHT11 ou d'un test IA.

    Paramètres :
      ant_id : identifiant de l'antenne (conservé pour compatibilité)
      prev   : mesure précédente (dict), ou None pour la première mesure

    Retour :
      dict {"temperature", "cpu", "signal", "latence", "disponibilite"}
      Toutes les valeurs sont dans les bornes normales (MRRW pur).
    """
    # Toujours retourner des mesures normales — jamais d'anomalie aléatoire
    return generer_mesures_normales(prev)


def job_simulation():
    """
    Cycle de simulation complet :
      1. Récupère toutes les antennes simulées (ISET Mahdia exclue)
      2. Récupère la dernière mesure de chaque antenne (pour la continuité MRRW)
      3. Génère de nouvelles mesures MRRW
      4. Insère en base puis déclenche l'IA ciblée par antenne
    """
    print(f"[SIM] Début du cycle — {datetime.now().strftime('%H:%M:%S')}")
    try:
        conn = connecter()
        cur  = conn.cursor()

        # Antennes simulées en état normal uniquement (ISET = DHT11, alertes = admin/IoT)
        cur.execute("""
            SELECT a.id,
                   s.temperature, s.cpu, s.signal, s.latence, s.disponibilite
            FROM antennes a
            LEFT JOIN antennes_statut s ON a.id = s.id
            WHERE a.nom != %s
              AND COALESCE(a.statut, 'normal') = 'normal'
        """, (ISET_MAHDIA_NOM,))
        antennes = cur.fetchall()
        now   = datetime.now()
        count = 0

        for row in antennes:
            ant_id, p_temp, p_cpu, p_signal, p_lat, p_dispo = row

            # Construire le dict de valeurs précédentes pour MRRW
            prev = None
            if p_temp is not None:
                prev = {
                    "temp":    float(p_temp),
                    "cpu":     float(p_cpu    or CIBLES["cpu"]),
                    "signal":  float(p_signal  or CIBLES["signal"]),
                    "latence": float(p_lat     or CIBLES["latence"]),
                    "dispo":   float(p_dispo   or CIBLES["dispo"]),
                }

            # Générer les nouvelles mesures (MRRW)
            m = generer_mesures(ant_id, prev)

            # Insérer la mesure — l'IA mettra à jour statut et score santé
            cur.execute("""
                INSERT INTO mesures
                    (antenne_id, temperature, cpu, signal, latence, disponibilite,
                     statut, date_mesure)
                VALUES (%s, %s, %s, %s, %s, %s, 'analyse_ia_en_cours', %s)
            """, (
                ant_id,
                m["temperature"], m["cpu"], m["signal"],
                m["latence"], m["disponibilite"],
                now
            ))
            count += 1

        conn.commit()
        cur.close()
        conn.close()

        # Analyse IA globale après insertion (toutes les antennes simulées du cycle)
        if count > 0:
            _declencher_ia_cycle()

        print(f"[SIM] {count} mesures insérées + IA globale (MRRW, ISET Mahdia exclue).")

    except Exception as e:
        print(f"[SIM ERREUR] {e}")
        return


def _declencher_ia_cycle() -> None:
    """Appelle l'API interne : IF → score santé → statuts (cycle 10 s)."""
    try:
        import requests
        res = requests.get(
            API_IA_URL,
            params={"source": "simulation"},
            timeout=120,
        )
        if res.status_code != 200:
            print(f"[IA] Cycle simulation — HTTP {res.status_code}")
    except Exception as e:
        print(f"[IA] Cycle simulation — {e}")


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
    print("=" * 60)
    print("  GEO-TÉLÉCOM NOC — Simulateur MRRW")
    print(f"  Intervalle       : {INTERVALLE_SECONDES} secondes")
    print(f"  Alpha MRRW       : {ALPHA}")
    print(f"  Cibles normales  : Temp={CIBLES['temp']}°C | CPU={CIBLES['cpu']}%")
    print(f"                     Signal={CIBLES['signal']}dBm | Latence={CIBLES['latence']}ms")
    print(f"                     Disponibilité={CIBLES['dispo']}%")
    print(f"  Antenne exclue   : '{ISET_MAHDIA_NOM}' (données DHT11 réelles)")
    print("=" * 60)

    attendre_api()
    job_simulation()  # Premier cycle immédiat au démarrage
    schedule.every(INTERVALLE_SECONDES).seconds.do(job_simulation)

    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        print("[STOP] Simulateur arrêté proprement.")


if __name__ == "__main__":
    demarrer()