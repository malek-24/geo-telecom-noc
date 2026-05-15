# ARCHITECTURE COMPLÈTE DU PROJET PFE (NOC TÉLÉCOM)

Ce document correspond à la structure complète de votre architecture (basée sur le Chapitre III). Il contient tous les éléments techniques de l'infrastructure géospatiale et logicielle pour votre rapport final.

---

## Chapitre III : Mise en place de l’infrastructure et intégration des outils géospatiaux

### Introduction
L'objectif du Sprint 1 est la mise en place d'une infrastructure solide, modulaire et évolutive. Le socle technique repose sur la conteneurisation via **Docker**, permettant de faire communiquer une base de données spatiales (PostgreSQL/PostGIS), un serveur cartographique (GeoServer), un catalogue de métadonnées (GeoNetwork) et nos applications métiers (API Flask et Frontend React). Ce sprint est le point de départ vital qui soutiendra toutes les futures fonctionnalités d'intelligence artificielle et de supervision NOC.

---

### 3.1 Backlog du Sprint 1
1. **Installation et configuration de Docker** : Création du réseau virtuel `projet-tt_sig_net` et du fichier `docker-compose.yml` unifié.
2. **Déploiement de GeoNetwork** : Installation de la version 3.12.12 pour le catalogage des métadonnées géographiques (port 8081).
3. **Installation et configuration de GeoServer** : Déploiement de l'image officielle OSGeo (version 2.25.2) sur le port 8080.
4. **Configuration de PostgreSQL/PostGIS** : Initialisation de la base de données relationnelle et spatiale `antennes_mahdia` (port 6000 mappé vers 5432).
5. **Intégration des données géographiques des antennes** : Création du script d'initialisation SQL et exécution d'un script Python (`geoserver_setup.py`) pour la synchronisation automatique des 127 antennes.
6. **Configuration de la communication entre GeoServer et PostgreSQL/PostGIS** : Création d'un "Datastore" PostGIS sécurisé via l'API REST de GeoServer.
7. **Configuration d’Elasticsearch avec GeoNetwork** : Indexation rapide des métadonnées pour améliorer la recherche spatiale.

---

### 3.2 Analyse

#### 3.2.1 Diagramme de cas d’utilisation
Les acteurs principaux interagissent avec l'infrastructure géospatiale selon trois grands axes :
- **Gérer les antennes** (Ajout, suppression, mise à jour des coordonnées).
- **Visualiser les données géographiques** (Affichage interactif des points sur la carte).
- **Consulter les couches cartographiques** (Accès aux couches WMS fournies par GeoServer).

#### 3.2.2 Description du cas d’utilisation : Gestion des antennes
- **Acteur** : Administrateur / Script d'initialisation.
- **Description** : Permet de définir les métadonnées (Nom, Zone, Type) et les coordonnées géographiques (Longitude, Latitude) d'une antenne relais.
- **Préconditions** : L'accès à la base de données PostgreSQL doit être valide, et l'extension PostGIS activée.
- **Postconditions** : L'antenne est convertie en géométrie de type `Point (SRID 4326)` et publiée sur GeoServer.

#### 3.2.3 Description du cas d’utilisation : Consultation des données géographiques
- **Acteur** : Modérateur NOC / Ingénieur.
- **Description** : L'utilisateur ouvre la carte Leaflet sur l'application React pour superviser le réseau.
- **Résultat attendu** : Affichage d'une carte fluide avec des marqueurs positionnés de façon exacte, interrogeables en temps réel pour connaître l'état de l'antenne.

---

### 3.3 Conception

#### 3.3.1 Diagrammes de séquence
*Interactions utilisateur – GeoServer – GeoNetwork – Base de données*
1. L'Utilisateur charge la page "Carte".
2. Le Frontend demande à **GeoServer** les "Tuiles" de la carte (format WMS).
3. GeoServer interroge la base de données **PostGIS** pour récupérer les géométries.
4. Parallèlement, l'utilisateur peut consulter les métadonnées de l'antenne : le système interroge **GeoNetwork**.
5. Les réponses sont fusionnées et affichées sur l'interface graphique.

#### 3.3.2 Diagramme de classes
L'architecture de données repose sur 3 entités principales :
- **Antenne** : Entité métier contenant les spécificités télécoms (id, nom, type, date_installation, statut).
- **Localisation (Géométrie)** : Gérée par PostGIS (type `GEOMETRY`). Stocke les coordonnées X/Y (SRID 4326).
- **Site / Zone** : Attribut de regroupement géographique (ex: Mahdia Nord, Mahdia Sud).

#### 3.3.3 Schéma relationnel et dictionnaire de données
- **Tables** : `antennes` (id, nom, zone, lat, lon, geom), `mesures` (id, antenne_id, température, CPU, trafic...), `incidents`.
- **Relations** : Une antenne possède `0..n` mesures et `0..n` incidents.
- **Structure des données géographiques** : Les données sont formatées dynamiquement. Le serveur cartographique convertit ces coordonnées en images WMS superposables sur OpenStreetMap.

---

### 3.4 Réalisation

#### 3.4.1 Architecture logique (diagramme de composants)
Le cœur de la réalisation repose sur 4 conteneurs indépendants mais interconnectés :
- **Docker** : L'hyperviseur réseau gérant le domaine interne.
- **GeoServer** : Le moteur de rendu cartographique standardisé de l'OGC.
- **GeoNetwork** : Le catalogue conforme aux normes ISO19115/19139.
- **PostgreSQL/PostGIS** : L'entrepôt persistant des données brutes et géographiques.

#### 3.4.2 Installation et configuration des outils
- **Déploiement Docker** : Lancement d'une seule commande `docker-compose up -d` pour orchestrer l'infrastructure.
- **Configuration PostgreSQL/PostGIS** : Création automatique d'un trigger SQL permettant de populer le champ géométrie (`geom`) à chaque insertion de Latitude/Longitude.
- **Configuration GeoServer** : Automatisation via Python (`geoserver_setup.py`) pour la déclaration de "l'Espace de travail" (Workspace) et du "Stockage de données" (Datastore PostGIS).
- **Configuration GeoNetwork / Elasticsearch** : Automatisation via Python (`geonetwork_metadata.py`) pour injecter les fiches descriptives au format XML standard.

#### 3.4.3 Description des interfaces
- **Interface GeoNetwork** : Portail de recherche accessible sur le port 8081 permettant de trouver des "fiches" sur les antennes.
- **Interface GeoServer** : Panel d'administration accessible sur le port 8080 pour la gestion de l'esthétique (styles SLD) des antennes.
- **Visualisation des couches géographiques** : Sur le dashboard (React.js), utilisation de `<WMSTileLayer>` combiné à l'API asynchrone pour marier cartographie stricte et télémétrie en direct.

---

### 3.5 Tests et validation
- **Test des conteneurs Docker** : Validation avec la commande `docker ps` confirmant l'état "(healthy)" des différents moteurs.
- **Validation de la connexion PostgreSQL/PostGIS** : Exécution de requêtes spatiales comme `ST_AsGeoJSON(geom)` pour s'assurer que les coordonnées se convertissent bien en vecteurs.
- **Validation GeoServer** : Utilisation de "Layer Preview" d'OpenLayers prouvant que le flux WMS se dessine sans erreur.
- **Validation GeoNetwork** : Accès direct au catalogue confirmant l'indexation réussie des 127 métadonnées d'antennes de Mahdia.

---

### Conclusion
**Résultats du Sprint 1** : L'objectif a été pleinement atteint. La mise en place de cette infrastructure géospatiale (Docker, PostgreSQL/PostGIS, GeoServer et GeoNetwork) constitue un socle robuste. La réussite de ce sprint garantit que les futures opérations du projet, notamment l'intégration du Machine Learning et le développement du tableau de bord NOC, s'appuieront sur des données cartographiques précises, fiables et performantes.
