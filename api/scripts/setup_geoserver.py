import requests
from requests.auth import HTTPBasicAuth
import time

GEOSERVER_URL = "http://geoserver:8080/geoserver/rest"
AUTH = HTTPBasicAuth('admin', 'geoserver')

def setup_geoserver():
    print("--- Configuration Automatisée de GeoServer ---")
    
    # 1. Créer le Workspace 'mahdia'
    print("[1/3] Création du Workspace 'mahdia'...")
    requests.post(
        f"{GEOSERVER_URL}/workspaces",
        json={"workspace": {"name": "mahdia"}},
        auth=AUTH
    )

    # 2. Créer le DataStore PostGIS
    print("[2/3] Connexion à la base PostGIS...")
    ds_payload = {
        "dataStore": {
            "name": "postgis_mahdia",
            "connectionParameters": {
                "entry": [
                    {"@key": "host", "$": "postgres"},
                    {"@key": "port", "$": "5432"},
                    {"@key": "database", "$": "antennes_mahdia"},
                    {"@key": "user", "$": "postgres"},
                    {"@key": "passwd", "$": "postgres"},
                    {"@key": "dbtype", "$": "postgis"},
                    {"@key": "schema", "$": "public"}
                ]
            }
        }
    }
    requests.post(
        f"{GEOSERVER_URL}/workspaces/mahdia/datastores",
        json=ds_payload,
        auth=AUTH
    )

    # 3. Publier la couche 'antennes_geo'
    print("[3/3] Publication de la couche 'antennes_geo'...")
    layer_payload = {
        "featureType": {
            "name": "antennes_geo",
            "nativeName": "antennes_geo",
            "title": "Antennes Réseau Mahdia",
            "srs": "EPSG:4326"
        }
    }
    requests.post(
        f"{GEOSERVER_URL}/workspaces/mahdia/datastores/postgis_mahdia/featuretypes",
        json=layer_payload,
        auth=AUTH
    )

    print("\n✅ GeoServer est prêt ! Les services WMS sont disponibles sur port 8081.")

if __name__ == "__main__":
    setup_geoserver()
