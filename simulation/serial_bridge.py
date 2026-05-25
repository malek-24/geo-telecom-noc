"""
serial_bridge.py — Passerelle Serial (Arduino Uno) → API Flask
================================================================
GEO-TELECOM NOC — Antenne IoT ISET Mahdia
PFE Licence 3 — Reseaux & Telecommunications 2025/2026

Fonctionnement :
  1. Au démarrage : récupère dynamiquement l'ID de l'antenne 'ISET Mahdia'
     via GET /iot/antenne/lookup?nom=ISET+Mahdia
     (si l'antenne n'existe pas, elle est créée automatiquement)
  2. Se connecte au port Serial de l'Arduino Uno (USB)
  3. Lit chaque ligne JSON envoyée par le sketch DHT11
  4. Envoie les données à l'API Flask via POST /iot/mesure
  5. L'IA Isolation Forest analyse automatiquement les nouvelles mesures

Usage :
  python serial_bridge.py
  python serial_bridge.py --port COM3 --api http://localhost:7000

Dependances :
  pip install pyserial requests

Format JSON attendu depuis l'Arduino :
  {"antenne_id": 121, "temperature": 28.5}

  Note : L'humidite n'est plus envoyee par l'Arduino.
         Seule la temperature exterieure de l'antenne est transmise.
"""

import sys
import json
import time
import argparse
import requests
import serial
import serial.tools.list_ports

# ----------------------------------------------------------------
#  CONFIGURATION PAR DEFAUT
# ----------------------------------------------------------------

SERIAL_PORT = "COM3"                      # Modifier selon votre systeme
BAUD_RATE   = 115200                      # Doit correspondre au sketch Arduino
API_URL     = "http://localhost:7000"     # URL de l'API Flask (port Docker)
API_KEY     = "arduino-noc-secret-2026"    # Cle IoT (IOT_API_KEY dans .env)
TIMEOUT_API = 10                          # Timeout requete HTTP (secondes)

# Nom de l'antenne physique — l'ID est récupéré dynamiquement depuis la BD
NOM_ANTENNE_IOT   = "ISET Mahdia"
LAT_ANTENNE_IOT   = 35.522473
LON_ANTENNE_IOT   = 11.030388

# L'ID réel sera renseigné par recuperer_antenne_id() au démarrage
_antenne_id_cache = None


# ----------------------------------------------------------------
#  RECUPERATION DYNAMIQUE DE L'ID DE L'ANTENNE
# ----------------------------------------------------------------

def recuperer_antenne_id(api_url: str, max_tentatives: int = 10, delai: int = 3) -> int:
    """
    Récupère l'ID de l'antenne 'ISET Mahdia' depuis la base de données
    via l'endpoint GET /iot/antenne/lookup.

    Si l'antenne n'existe pas, elle est créée automatiquement avec les
    coordonnées : lat=35.522473, lon=11.030388 (ISET Mahdia).

    Retourne l'ID réel de la base (ex: 121).
    Evite de coder l'ID en dur dans le code.
    """
    nom = NOM_ANTENNE_IOT
    url = (
        f"{api_url}/iot/antenne/lookup"
        f"?nom={nom.replace(' ', '+')}"
        f"&create=1&lat={LAT_ANTENNE_IOT}&lon={LON_ANTENNE_IOT}"
    )
    headers = {"X-API-Key": API_KEY}

    for tentative in range(1, max_tentatives + 1):
        try:
            resp = requests.get(url, headers=headers, timeout=5)
            if resp.status_code in (200, 201):
                data = resp.json()
                ant_id = data.get("id")
                if ant_id:
                    created = data.get("created", False)
                    action  = "créée" if created else "trouvée"
                    print(f"[IoT] Antenne '{nom}' {action} en base — ID = {ant_id}")
                    return int(ant_id)
            print(f"[IoT] Tentative {tentative}/{max_tentatives} — HTTP {resp.status_code}")
        except requests.exceptions.ConnectionError:
            print(f"[IoT] Tentative {tentative}/{max_tentatives} — API inaccessible, nouvel essai dans {delai}s")
        except Exception as e:
            print(f"[IoT] Tentative {tentative}/{max_tentatives} — {e}")
        time.sleep(delai)

    # Fallback : utiliser l'ID attendu après les 120 antennes simulées
    print(f"[IoT] AVERTISSEMENT : ID non récupéré depuis la BD.")
    print(f"[IoT] Utilisation de l'ID par défaut (121) — vérifier l'API.")
    print(f"[IoT] Commande de vérification : SELECT id FROM antennes WHERE nom = '{nom}';")
    return 121



def detecter_port_arduino():
    """
    Tente de detecter automatiquement le port de l'Arduino Uno.
    Recherche les ports avec 'Arduino' ou 'CH340' dans la description.
    """
    ports = serial.tools.list_ports.comports()
    for port in ports:
        desc = (port.description or "").lower()
        mfr  = (port.manufacturer or "").lower()
        if any(k in desc or k in mfr for k in ["arduino", "ch340", "ch341", "ftdi"]):
            print(f"[SERIAL] Arduino detecte automatiquement : {port.device}")
            return port.device
    return None


# ----------------------------------------------------------------
#  ENVOI D'UNE MESURE A L'API
# ----------------------------------------------------------------

def envoyer_mesure(data: dict) -> bool:
    """
    Envoie une mesure JSON a l'endpoint /iot/mesure de l'API Flask.
    Retourne True si la mesure est acceptee (HTTP 201), False sinon.
    """
    url = f"{API_URL}/iot/mesure"
    headers = {
        "Content-Type": "application/json",
        "X-API-Key":    API_KEY,
    }
    try:
        resp = requests.post(url, json=data, headers=headers, timeout=TIMEOUT_API)
        if resp.status_code == 201:
            body = resp.json()
            print(f"[API] OK — {body.get('message', 'Mesure acceptee')}")
            return True
        else:
            print(f"[API] ERREUR HTTP {resp.status_code} — {resp.text[:200]}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"[API] ERREUR — Impossible de joindre {url}")
        print("[API]   Verifiez que Docker est en cours d'execution (docker-compose up)")
        return False
    except Exception as e:
        print(f"[API] ERREUR — {e}")
        return False


# ----------------------------------------------------------------
#  TRAITEMENT D'UNE LIGNE SERIE
# ----------------------------------------------------------------

def traiter_ligne(ligne: str) -> bool:
    """
    Traite une ligne recue du Serial.
    - Ignore les lignes commencant par '#'
    - Parse le JSON
    - Remplace automatiquement l'antenne_id par l'ID réel
      récupéré depuis PostgreSQL (ISET Mahdia)
    - Envoie la mesure à l'API Flask

    Retourne True si la mesure est acceptée.
    """

    global _antenne_id_cache

    ligne = ligne.strip()

    # Ignorer les lignes vides
    if not ligne:
        return False

    # Logs Arduino
    if ligne.startswith("#"):
        print(f"[ARDUINO] {ligne[1:].strip()}")
        return False

    # Décodage JSON
    try:
        data = json.loads(ligne)

    except json.JSONDecodeError:
        print(f"[SERIAL] Ligne non-JSON ignorée : {ligne[:80]}")
        return False

    # Forcer l'utilisation de l'ID réel de la base
    if _antenne_id_cache is not None:
        data["antenne_id"] = _antenne_id_cache

    # Vérification des champs obligatoires
    if "temperature" not in data:
        print(f"[SERIAL] Champ temperature manquant : {data}")
        return False

    # Affichage console
    temp = data.get("temperature", "?")
    aid = data.get("antenne_id", "?")

    print(
        f"[DHT11] Antenne {aid} "
        f"(ISET Mahdia) — Temp={temp}°C "
        f"(temperature exterieure)"
    )

    # Envoi à l'API
    return envoyer_mesure(data)


# ----------------------------------------------------------------
#  BOUCLE PRINCIPALE
# ----------------------------------------------------------------

def demarrer(port: str, api_url: str):
    """Boucle principale : lit le Serial et envoie a l'API."""
    global API_URL, _antenne_id_cache
    API_URL = api_url

    # ── Étape 1 : Récupérer l'ID de l'antenne depuis la BD ──────
    # L'ID est récupéré dynamiquement — jamais codé en dur
    print("[IoT] Récupération de l'ID de l'antenne 'ISET Mahdia' depuis la base...")
    antenne_id = recuperer_antenne_id(api_url)
    _antenne_id_cache = antenne_id

    # Detection automatique si le port n'est pas specifie
    if not port:
        port = detecter_port_arduino()
        if not port:
            print("[ERREUR] Aucun Arduino detecte. Specifiez le port avec --port COM3")
            print("[INFO]   Ports disponibles :")
            for p in serial.tools.list_ports.comports():
                print(f"           {p.device} — {p.description}")
            sys.exit(1)

    print("=" * 55)
    print("  GEO-TELECOM NOC — Passerelle Serial -> API")
    print(f"  Antenne : {NOM_ANTENNE_IOT} (ID BD = {antenne_id})")
    print(f"  Port Serial : {port} @ {BAUD_RATE} baud")
    print(f"  API URL     : {API_URL}")
    print("=" * 55)
    print("[INFO] Appuyez sur Ctrl+C pour arreter\n")

    # Connexion au port Serial
    try:
        ser = serial.Serial(port, BAUD_RATE, timeout=2)
        time.sleep(2)  # Attendre la reinitialisation de l'Arduino
        print(f"[SERIAL] Connexion etablie sur {port}\n")
    except serial.SerialException as e:
        print(f"[ERREUR] Impossible d'ouvrir {port} : {e}")
        print("[INFO]   Verifiez que l'Arduino est branche et que le port est correct.")
        sys.exit(1)

    # Compteurs
    nb_envoyes = 0
    nb_erreurs = 0

    try:
        while True:
            try:
                ligne = ser.readline().decode("utf-8", errors="ignore")
                if ligne:
                    ok = traiter_ligne(ligne)
                    if ok:
                        nb_envoyes += 1
                    elif not ligne.strip().startswith("#") and ligne.strip():
                        nb_erreurs += 1
            except serial.SerialException as e:
                print(f"[SERIAL] Erreur de lecture : {e}")
                time.sleep(5)

    except KeyboardInterrupt:
        print(f"\n[STOP] Passerelle arretee — Envoyes: {nb_envoyes}  Erreurs: {nb_erreurs}")
    finally:
        ser.close()



# ----------------------------------------------------------------
#  POINT D'ENTREE
# ----------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Passerelle Serial Arduino → API Flask (ISET Mahdia IoT)"
    )
    parser.add_argument(
        "--port", default=None,
        help="Port Serial de l'Arduino (ex: COM3, /dev/ttyUSB0). "
             "Detection automatique si non specifie."
    )
    parser.add_argument(
        "--api", default=API_URL,
        help=f"URL de base de l'API Flask (defaut: {API_URL})"
    )
    args = parser.parse_args()
    demarrer(args.port, args.api)
