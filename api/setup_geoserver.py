import requests
from requests.auth import HTTPBasicAuth
import time

GEOSERVER_URL = "http://geoserver:8080/geoserver/rest"
AUTH = HTTPBasicAuth('admin', 'geoserver')

def setup_geoserver():
    print("--- Nettoyage et Configuration GeoServer NOC Mahdia ---")
    
    # 0. Supprimer le Workspace s'il existe (pour repartir à neuf)
    print("[0] Nettoyage du workspace 'mahdia'...")
    requests.delete(f"{GEOSERVER_URL}/workspaces/mahdia?recurse=true", auth=AUTH)

    # 1. Créer le Workspace 'mahdia'
    print("[1] Création du Workspace 'mahdia'...")
    requests.post(
        f"{GEOSERVER_URL}/workspaces",
        json={"workspace": {"name": "mahdia"}},
        auth=AUTH
    )

    # 2. Créer le DataStore PostGIS
    print("[2] Configuration du DataStore 'postgis_mahdia'...")
    ds_payload = {
        "dataStore": {
            "name": "postgis_mahdia",
            "connectionParameters": {
                "entry": [
                    {"@key": "host", "$": "postgres"},
                    {"@key": "port", "$": "5432"},
                    {"@key": "database", "$": "antennes_mahdia"},
                    {"@key": "user", "$": "postgres"},
                    {"@key": "passwd", "$": "1234"},
                    {"@key": "dbtype", "$": "postgis"},
                    {"@key": "schema", "$": "public"}
                ]
            }
        }
    }
    r = requests.post(
        f"{GEOSERVER_URL}/workspaces/mahdia/datastores",
        json=ds_payload,
        auth=AUTH
    )
    if r.status_code != 201:
        print(f"❌ Erreur DataStore: {r.text}")
        return

    # 3. Publier les couches
    layers = [
        ("antennes_tt", "Points Antennes Tunisie Telecom"),
        ("couverture_reseau", "Couverture Réseau SIG"),
        ("incidents_v", "Incidents Critiques Actifs"),
        ("zones_critiques", "Zones de Risque Elevé")
    ]

    for layer_name, layer_title in layers:
        print(f"[3] Publication de la couche '{layer_name}'...")
        payload = {
            "featureType": {
                "name": layer_name,
                "nativeName": layer_name,
                "title": layer_title,
                "srs": "EPSG:4326"
            }
        }
        r = requests.post(
            f"{GEOSERVER_URL}/workspaces/mahdia/datastores/postgis_mahdia/featuretypes",
            json=payload,
            auth=AUTH
        )
        if r.status_code == 201:
            print(f"    ✅ Couche '{layer_name}' publiée.")
        else:
            print(f"    ❌ Erreur pour '{layer_name}': {r.text}")

    print("\n✅ Configuration SIG terminée avec succès.")

if __name__ == "__main__":
    print("Attente de GeoServer (15s)...")
    time.sleep(15)
    setup_geoserver()
