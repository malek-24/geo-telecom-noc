#!/usr/bin/env python3
"""
geoserver_setup.py — Configuration automatique de GeoServer
============================================================
Ce script configure GeoServer après son premier démarrage :
  1. Crée un espace de travail (workspace) "telecom_mahdia"
  2. Crée un magasin de données (datastore) PostGIS pointant sur
     notre base PostgreSQL
  3. Publie 3 couches géographiques :
       - antennes_geo        (toutes les antennes avec leur géométrie)
       - antennes_alertes    (antennes en état alerte/critique)
       - antennes_anomalies  (antennes détectées par Isolation Forest)

Usage :
    python geoserver_setup.py

Prérequis : GeoServer doit être démarré (http://localhost:8080/geoserver)
"""

import requests
import json
import sys
import time

# ─── Configuration ────────────────────────────────────────────
GEOSERVER_URL   = "http://localhost:8080/geoserver"
GS_USER         = "admin"
GS_PASSWORD     = "geoserver"

WORKSPACE       = "telecom_mahdia"
DATASTORE       = "postgis_antennes"

PG_HOST         = "postgres"   # nom du service Docker (reseau interne)
PG_PORT         = "5432"       # port interne Docker (pas 6000 qui est l'expose hote)
PG_DB           = "antennes_mahdia"
PG_USER         = "postgres"
PG_PASSWORD     = "1234"

HEADERS_JSON    = {"Content-Type": "application/json"}
HEADERS_XML     = {"Content-Type": "application/xml"}
AUTH            = (GS_USER, GS_PASSWORD)

# Couches à publier (table/vue PostgreSQL → nom de la couche GeoServer)
LAYERS = [
    {
        "name":        "antennes_geo",
        "native_name": "antennes_geo",
        "title":       "Antennes Télécom — Mahdia",
        "abstract":    "Toutes les antennes-relais 4G/5G du gouvernorat de Mahdia avec leur état de santé temps réel.",
        "srs":         "EPSG:4326"
    },
    {
        "name":        "antennes_statut",
        "native_name": "antennes_statut",
        "title":       "Statut des Antennes en Temps Réel",
        "abstract":    "Mesures les plus récentes par antenne (CPU, température, latence, disponibilité).",
        "srs":         "EPSG:4326"
    },
]

def wait_for_geoserver(max_tries=20, delay=10):
    """Attend que GeoServer soit prêt."""
    print("[...] Attente de GeoServer...")
    for i in range(max_tries):
        try:
            r = requests.get(f"{GEOSERVER_URL}/web/", timeout=5)
            if r.status_code < 500:
                print("[OK]  GeoServer est disponible.")
                return True
        except Exception:
            pass
        print(f"   Tentative {i+1}/{max_tries} -- reessai dans {delay}s...")
        time.sleep(delay)
    print("[ERR] GeoServer non disponible apres plusieurs tentatives.")
    return False


def create_workspace():
    """Crée le workspace 'telecom_mahdia' si inexistant."""
    url = f"{GEOSERVER_URL}/rest/workspaces"
    payload = {"workspace": {"name": WORKSPACE}}
    r = requests.post(url, auth=AUTH, headers=HEADERS_JSON,
                      data=json.dumps(payload))
    if r.status_code in (201, 200):
        print(f"[OK]  Workspace '{WORKSPACE}' cree.")
    elif r.status_code == 409:
        print(f"[i]   Workspace '{WORKSPACE}' existe deja.")
    else:
        print(f"[WARN] Workspace : {r.status_code} -- {r.text}")


def create_datastore():
    """Crée le datastore PostGIS pointant sur notre PostgreSQL."""
    url = f"{GEOSERVER_URL}/rest/workspaces/{WORKSPACE}/datastores"
    payload = {
        "dataStore": {
            "name": DATASTORE,
            "type": "PostGIS",
            "enabled": True,
            "connectionParameters": {
                "entry": [
                    {"@key": "host",     "$": PG_HOST},
                    {"@key": "port",     "$": PG_PORT},
                    {"@key": "database", "$": PG_DB},
                    {"@key": "user",     "$": PG_USER},
                    {"@key": "passwd",   "$": PG_PASSWORD},
                    {"@key": "dbtype",   "$": "postgis"},
                    {"@key": "schema",   "$": "public"},
                    {"@key": "Expose primary keys", "$": "true"},
                ]
            }
        }
    }
    r = requests.post(url, auth=AUTH, headers=HEADERS_JSON,
                      data=json.dumps(payload))
    if r.status_code in (201, 200):
        print(f"[OK]  Datastore PostGIS '{DATASTORE}' cree.")
    elif r.status_code == 409:
        print(f"[i]   Datastore '{DATASTORE}' existe deja.")
    else:
        print(f"[WARN] Datastore : {r.status_code} -- {r.text}")


def publish_layer(layer: dict):
    """Publie une couche (table/vue PostgreSQL) dans GeoServer."""
    url = (f"{GEOSERVER_URL}/rest/workspaces/{WORKSPACE}"
           f"/datastores/{DATASTORE}/featuretypes")
    payload = {
        "featureType": {
            "name":        layer["name"],
            "nativeName":  layer["native_name"],
            "title":       layer["title"],
            "abstract":    layer["abstract"],
            "srs":         layer["srs"],
            "enabled":     True,
        }
    }
    r = requests.post(url, auth=AUTH, headers=HEADERS_JSON,
                      data=json.dumps(payload))
    if r.status_code in (201, 200):
        print(f"[OK]  Couche '{layer['name']}' publiee.")
    elif r.status_code == 409:
        print(f"[i]   Couche '{layer['name']}' existe deja.")
    else:
        print(f"[WARN] Couche '{layer['name']}' : {r.status_code} -- {r.text}")


def main():
    if not wait_for_geoserver():
        sys.exit(1)

    print("\n--- Configuration GeoServer ---")
    create_workspace()
    create_datastore()

    print("\n--- Publication des couches ---")
    for layer in LAYERS:
        publish_layer(layer)

    print("\n--- Resume ---")
    print(f"  WMS GetCapabilities :")
    print(f"  {GEOSERVER_URL}/{WORKSPACE}/ows?service=WMS&version=1.3.0&request=GetCapabilities")
    print(f"\n  WFS GetCapabilities :")
    print(f"  {GEOSERVER_URL}/{WORKSPACE}/ows?service=WFS&version=2.0.0&request=GetCapabilities")
    print(f"\n  Couche WMS antennes_geo :")
    print(f"  {GEOSERVER_URL}/{WORKSPACE}/wms?service=WMS&version=1.1.0")
    print(f"    &request=GetMap&layers={WORKSPACE}:antennes_geo&bbox=...")
    print("\n[OK]  Configuration GeoServer terminee.")


if __name__ == "__main__":
    main()
