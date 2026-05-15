# Guide d'Intégration GIS — GeoServer & GeoNetwork
## Plateforme NOC Tunisie Telecom — PFE 2026

---

## Architecture GIS

```
PostgreSQL/PostGIS  ──►  GeoServer (WMS/WFS)  ──►  React Leaflet (Frontend)
       │                                                      │
       └──────────────────────────────────────────────────────┘
                                    │
                              GeoNetwork (CSW)
                         (Catalogue de métadonnées)
```

---

## Services et Ports

| Service         | URL                                        | Identifiants       |
|-----------------|--------------------------------------------|--------------------|
| **GeoServer**   | http://localhost:8080/geoserver            | admin / geoserver  |
| **GeoNetwork**  | http://localhost:8081/geonetwork           | admin / admin      |
| **PostgreSQL**  | localhost:6000                             | postgres / 1234    |
| **Frontend**    | http://localhost:3000                      | —                  |
| **API Flask**   | http://localhost:7000                      | —                  |

---

## Démarrage rapide

### 1. Démarrer tous les services

```bash
docker compose up -d
```

Attendre que tous les conteneurs soient `healthy` (environ 60 secondes).

### 2. Configurer GeoServer (automatique)

```bash
# Installer les dépendances Python si nécessaire
pip install requests

# Configurer GeoServer : workspace + datastore PostGIS + publication des couches
python geoserver_setup.py
```

Ce script crée automatiquement :
- Le workspace `telecom_mahdia`
- Le datastore PostGIS (connexion vers notre PostgreSQL)
- La publication des vues `antennes_geo` et `antennes_statut` en tant que couches WMS/WFS

### 3. Créer les métadonnées dans GeoNetwork

```bash
python geonetwork_metadata.py
```

Ce script insère dans GeoNetwork des fiches de métadonnées Dublin Core pour chaque couche télécom.

---

## Couches GeoServer publiées

### Couche 1 : `antennes_geo`
- **Source** : Vue PostGIS `antennes_geo` (toutes antennes + géométrie)
- **WMS** : `http://localhost:8080/geoserver/telecom_mahdia/wms?service=WMS&version=1.1.0&request=GetMap&layers=telecom_mahdia:antennes_geo`
- **WFS** : `http://localhost:8080/geoserver/telecom_mahdia/wfs?service=WFS&version=2.0.0&request=GetFeature&typeNames=telecom_mahdia:antennes_geo&outputFormat=application/json`

### Couche 2 : `antennes_statut`
- **Source** : Vue PostGIS `antennes_statut` (statut temps réel + métriques)
- **WMS** : `http://localhost:8080/geoserver/telecom_mahdia/wms?service=WMS&version=1.1.0&request=GetMap&layers=telecom_mahdia:antennes_statut`

---

## Intégration dans la carte React

La page `/carte` intègre les couches WMS GeoServer via `react-leaflet` :

1. Au chargement, le frontend tente de joindre GeoServer
2. Si GeoServer est actif → les couches WMS apparaissent dans le **contrôleur de couches** (coin supérieur droit de la carte)
3. Si GeoServer est hors ligne → la carte fonctionne normalement avec les marqueurs Leaflet (mode dégradé)

Le badge **"GeoServer WMS — Actif / Hors ligne"** en bas de la légende indique l'état du service en temps réel.

---

## Métadonnées GeoNetwork

GeoNetwork joue le rôle de **catalogue de métadonnées géographiques** (norme ISO 19115 / OGC CSW).

Chaque couche télécom est documentée avec :
- Titre et description
- Mots-clés techniques (NOC, télécom, antennes, Mahdia…)
- Emprise géographique (bbox)
- Fréquence de mise à jour
- Lien vers le service WMS correspondant
- Droits d'usage (académique PFE 2026)

### Moissonnage GeoServer → GeoNetwork

Pour lier GeoServer et GeoNetwork (optionnel, pour la soutenance) :

1. Ouvrir GeoNetwork : http://localhost:8081/geonetwork
2. Menu **Administration > Moissonnage**
3. Ajouter un moissonneur de type **OGC WMS 1.1.0**
4. URL du service : `http://geoserver:8080/geoserver/telecom_mahdia/wms`
   *(Utiliser le nom réseau Docker `geoserver`, pas `localhost`)*
5. Exécuter le moissonnage → GeoNetwork crée automatiquement les fiches

---

## Vérification de l'intégration

```bash
# Vérifier que GeoServer publie bien les couches
curl "http://localhost:8080/geoserver/telecom_mahdia/ows?service=WMS&version=1.3.0&request=GetCapabilities"

# Récupérer les antennes au format GeoJSON via WFS
curl "http://localhost:8080/geoserver/telecom_mahdia/wfs?service=WFS&version=2.0.0&request=GetFeature&typeNames=telecom_mahdia:antennes_geo&outputFormat=application/json&count=5"

# Vérifier les métadonnées dans GeoNetwork via CSW
curl "http://localhost:8081/geonetwork/srv/fre/csw?service=CSW&version=2.0.2&request=GetRecords&resultType=results&typeNames=csw:Record"
```

---

## Architecture finale complète

```
┌─────────────────────────────────────────────────────────────┐
│                     Docker Compose Network                  │
│                                                             │
│  ┌───────────┐    ┌───────────┐    ┌───────────────────┐   │
│  │  React    │    │   Flask   │    │  PostgreSQL        │   │
│  │  :3000    │◄──►│   API     │◄──►│  PostGIS :6000    │   │
│  │  Leaflet  │    │   :7000   │    │                   │   │
│  └─────┬─────┘    └───────────┘    └────────┬──────────┘   │
│        │                                    │              │
│        │ WMS      ┌──────────────┐          │              │
│        └─────────►│  GeoServer   │◄─────────┘              │
│                   │  :8080       │  (PostGIS DataStore)     │
│                   └──────────────┘                          │
│                                                             │
│                   ┌──────────────┐                          │
│                   │  GeoNetwork  │  (Catalogue CSW)         │
│                   │  :8081       │                          │
│                   └──────────────┘                          │
└─────────────────────────────────────────────────────────────┘
```
