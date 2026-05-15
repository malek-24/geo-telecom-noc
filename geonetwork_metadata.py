#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
geonetwork_metadata.py -- Creation des metadonnees dans GeoNetwork
===================================================================
Insere des fiches de metadonnees Dublin Core dans GeoNetwork pour
chaque couche geographique telecom publiee par GeoServer.

GeoNetwork : http://localhost:8081/geonetwork
Identifiants par defaut : admin / admin

Usage :
    python geonetwork_metadata.py
"""

import requests
import json
import time
import sys
from datetime import date

# --- Configuration ---
GEONETWORK_URL = "http://localhost:8081/geonetwork"
GN_USER        = "admin"
GN_PASSWORD    = "admin"

GEOSERVER_WMS  = "http://localhost:8080/geoserver/telecom_mahdia/wms"
TODAY          = date.today().isoformat()

# --- Couches a documenter ---
METADATA_RECORDS = [
    {
        "title":    "Antennes Telecom 4G/5G - Gouvernorat de Mahdia",
        "abstract": (
            "Couche geographique des antennes-relais du reseau Tunisie Telecom "
            "deployees dans le gouvernorat de Mahdia (Tunisie). "
            "Chaque entite represente une antenne physique avec son etat de sante "
            "calcule a partir des metriques reseau (CPU, temperature, disponibilite, latence). "
            "Mise a jour automatiquement toutes les 30 minutes par le systeme NOC."
        ),
        "layer":    "telecom_mahdia:antennes_geo",
        "keywords": ["telecom", "antennes", "4G", "5G", "Mahdia", "Tunisie Telecom", "NOC"],
        "source":   "Simulation NOC - Plateforme PFE 2026",
        "language": "fre",
        "srs":      "EPSG:4326 (WGS 84)",
        "bbox":     {"west": 10.6, "east": 11.2, "south": 35.0, "north": 35.7},
    },
    {
        "title":    "Statut Temps Reel des Antennes - Vue NOC Mahdia",
        "abstract": (
            "Vue agregee du statut le plus recent de chaque antenne telecom du gouvernorat de Mahdia. "
            "Affiche les indicateurs de performance reseau : RSSI, latence, taux de perte de paquets, "
            "charge CPU, temperature et disponibilite. "
            "Les anomalies detectees par l'algorithme Isolation Forest sont integrees dans cet attribut."
        ),
        "layer":    "telecom_mahdia:antennes_statut",
        "keywords": ["supervision", "statut", "NOC", "anomalie", "Isolation Forest", "temps reel"],
        "source":   "Base de donnees NOC PostgreSQL/PostGIS - Vue antennes_statut",
        "language": "fre",
        "srs":      "EPSG:4326 (WGS 84)",
        "bbox":     {"west": 10.6, "east": 11.2, "south": 35.0, "north": 35.7},
    },
]


def build_dc_xml(record):
    """Construit un enregistrement Dublin Core simple."""
    keywords_xml = "\n    ".join(
        "<dc:subject>{}</dc:subject>".format(kw) for kw in record["keywords"]
    )
    bbox = record["bbox"]
    return """<?xml version="1.0" encoding="UTF-8"?>
<simpledc xmlns:dc="http://purl.org/dc/elements/1.1/"
          xmlns:dct="http://purl.org/dc/terms/">
  <dc:title>{title}</dc:title>
  <dc:description>{abstract}</dc:description>
  <dc:language>{language}</dc:language>
  <dc:type>dataset</dc:type>
  <dc:source>{source}</dc:source>
  {keywords}
  <dc:date>{today}</dc:date>
  <dct:created>{today}</dct:created>
  <dct:modified>{today}</dct:modified>
  <dc:coverage>
    Emprise : Longitude {west} a {east}, Latitude {south} a {north}
    | Systeme de reference : {srs}
    | Gouvernorat de Mahdia, Tunisie
  </dc:coverage>
  <dc:relation>WMS:{wms}?service=WMS&amp;version=1.1.0&amp;request=GetMap&amp;layers={layer}</dc:relation>
  <dc:rights>Usage academique - PFE 2026 - Tunisie Telecom NOC</dc:rights>
  <dc:publisher>Tunisie Telecom - Projet PFE Supervision Reseau NOC</dc:publisher>
</simpledc>""".format(
        title    = record["title"],
        abstract = record["abstract"],
        language = record["language"],
        source   = record["source"],
        keywords = keywords_xml,
        today    = TODAY,
        west     = bbox["west"], east  = bbox["east"],
        south    = bbox["south"], north = bbox["north"],
        srs      = record["srs"],
        wms      = GEOSERVER_WMS,
        layer    = record["layer"],
    )


def wait_for_geonetwork(max_tries=15, delay=10):
    """Attend que GeoNetwork soit disponible."""
    print("[...] Attente de GeoNetwork...")
    for i in range(max_tries):
        try:
            r = requests.get(
                "{}/srv/fre/info?type=me".format(GEONETWORK_URL), timeout=8
            )
            if r.status_code < 500:
                print("[OK]  GeoNetwork est disponible.")
                return True
        except Exception:
            pass
        print("   Tentative {}/{} - reessai dans {}s...".format(i + 1, max_tries, delay))
        time.sleep(delay)
    print("[ERR] GeoNetwork non disponible.")
    return False


def get_xsrf_token(session):
    """Connexion + recuperation du token XSRF."""
    try:
        r = session.post(
            "{}/srv/api/user/login".format(GEONETWORK_URL),
            json={"username": GN_USER, "password": GN_PASSWORD},
            headers={"Accept": "application/json"},
            timeout=15,
        )
        token = (
            session.cookies.get("XSRF-TOKEN")
            or r.headers.get("X-XSRF-TOKEN")
            or ""
        )
        print("[OK]  Connexion GeoNetwork OK (token: {})".format(token[:12] or "cookie-based"))
        return token
    except Exception as e:
        print("[WARN] Token XSRF non obtenu : {}".format(e))
        return ""


def insert_metadata(session, csrf_token, record):
    """Insere une fiche Dublin Core dans GeoNetwork."""
    xml_content = build_dc_xml(record)
    headers = {"Content-Type": "application/xml", "Accept": "application/json"}
    if csrf_token:
        headers["X-XSRF-TOKEN"] = csrf_token

    try:
        r = session.put(
            "{}/srv/api/records".format(GEONETWORK_URL),
            data=xml_content.encode("utf-8"),
            headers=headers,
            params={"metadataType": "METADATA", "schema": "dublin-core"},
            timeout=30,
        )
        title_short = record["title"][:55]
        if r.status_code in (200, 201):
            print("  [OK]  '{}...' insere (HTTP {})".format(title_short, r.status_code))
            return True
        else:
            print("  [WARN] '{}' - HTTP {}: {}".format(title_short, r.status_code, r.text[:150]))
            return False
    except Exception as e:
        print("  [ERR]  Erreur lors de l'insertion : {}".format(e))
        return False


def print_summary():
    print("\n--- URLs utiles ---")
    print("  Catalogue GeoNetwork : {}".format(GEONETWORK_URL))
    print("  API CSW              : {}/srv/fre/csw".format(GEONETWORK_URL))
    print("\n--- Moissonnage GeoServer dans GeoNetwork ---")
    print("  Administration > Moissonnage > OGC WMS 1.1.0")
    print("  URL : http://geoserver:8080/geoserver/telecom_mahdia/wms")


def main():
    if not wait_for_geonetwork():
        print("\n[HINT] Verifiez que GeoNetwork est demarre : docker compose up geonetwork")
        sys.exit(1)

    session = requests.Session()
    session.auth = (GN_USER, GN_PASSWORD)
    csrf = get_xsrf_token(session)

    print("\n--- Insertion des fiches de metadonnees ---")
    ok = sum(insert_metadata(session, csrf, r) for r in METADATA_RECORDS)
    print("\n  {}/{} fiche(s) inseree(s) avec succes.".format(ok, len(METADATA_RECORDS)))
    print_summary()


if __name__ == "__main__":
    main()
