"""
simulate_dht11_docker.py — Simulation DHT11 dans Docker (sans USB)
Affiche les mêmes logs que serial_bridge.py pour la démo / test Docker Desktop.
"""
import os
import random
import time
import requests

API_URL = os.getenv("API_URL", "http://api:5000")
API_KEY = os.getenv("IOT_API_KEY", "arduino-noc-secret-2026")
ANTENNE_ID = int(os.getenv("IOT_ANTENNE_ID", "121"))
INTERVAL = float(os.getenv("IOT_INTERVAL_SEC", "3"))


def lookup_id():
    url = (
        f"{API_URL}/iot/antenne/lookup"
        f"?nom=ISET+Mahdia&create=1&lat=35.522473&lon=11.030388"
    )
    try:
        r = requests.get(url, headers={"X-API-Key": API_KEY}, timeout=5)
        if r.status_code in (200, 201):
            return int(r.json().get("id", ANTENNE_ID))
    except Exception as e:
        print(f"[IoT] Lookup impossible : {e}")
    return ANTENNE_ID


def main():
    ant_id = lookup_id()
    print("=" * 55)
    print("  GEO-TELECOM NOC — Simulateur DHT11 (Docker)")
    print(f"  Antenne : ISET Mahdia (ID = {ant_id})")
    print(f"  API     : {API_URL}")
    print(f"  Intervalle : {INTERVAL}s")
    print("=" * 55)

    temp = 27.5
    while True:
        temp = round(temp + random.uniform(-0.2, 0.3), 1)
        temp = max(24.0, min(50.0, temp))

        print(
            f"[DHT11] Antenne {ant_id} "
            f"(ISET Mahdia) — Temp={temp}°C "
            f"(temperature exterieure)"
        )

        try:
            r = requests.post(
                f"{API_URL}/iot/mesure",
                json={"antenne_id": ant_id, "temperature": temp},
                headers={
                    "Content-Type": "application/json",
                    "X-API-Key": API_KEY,
                },
                timeout=10,
            )
            if r.status_code == 201:
                print("[API] OK — Mesure IoT reçue pour ISET Mahdia")
            else:
                print(f"[API] ERREUR HTTP {r.status_code} — {r.text[:120]}")
        except Exception as e:
            print(f"[API] ERREUR — {e}")

        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()
