# Rapport de Projet de Fin d'Études (PFE)
## Plateforme Intelligente de Supervision des Infrastructures Télécoms (NOC)

---

## 1. PRÉSENTATION DU PROJET

### 1.1 Contexte du Projet
Dans un monde de plus en plus connecté, la stabilité et la fiabilité des réseaux de télécommunication sont devenues des enjeux majeurs. Les opérateurs télécoms déploient des milliers d'antennes-relais pour garantir une couverture continue. Cependant, ces équipements sont sujets à de multiples défaillances (pannes matérielles, surcharges réseau, coupures d'énergie, etc.).

### 1.2 Problématique de Supervision (NOC)
La gestion de ces infrastructures s'opère généralement depuis un centre de contrôle réseau (NOC - *Network Operations Center*). Historiquement, les opérateurs du NOC surveillent les équipements via des seuils fixes d'alerte, ce qui génère souvent des "tempêtes d'alarmes" (faux positifs) et rend difficile l'identification des véritables problèmes complexes ou silencieux.

### 1.3 Objectif et Apport de l'Intelligence Artificielle
L'objectif de ce projet est de concevoir et développer une plateforme centralisée de supervision réseau, en y intégrant un module d'Intelligence Artificielle (IA). L'utilisation de l'IA (notamment pour la détection d'anomalies) permet d'analyser le comportement global des indicateurs de performance (KPIs) et d'isoler des défaillances non détectables par des seuils traditionnels. Ainsi, le système gagne en précision, réduit le bruit et facilite la prise de décision.

---

## 2. OBJECTIFS DU PROJET

### 2.1 Objectif Global
Développer une solution logicielle complète, fonctionnelle et ergonomique permettant de superviser l'état de santé d'un parc de 120 antennes télécoms réparties sur plusieurs zones.

### 2.2 Objectifs Techniques
- **Centralisation des données** : Collecter et stocker les métriques télécoms dans une base de données relationnelle unique.
- **Analyse temps réel** : Identifier automatiquement les comportements suspects à l'aide d'un algorithme de Machine Learning.
- **Visualisation claire** : Fournir une interface utilisateur réactive (tableaux de bord, cartographie, graphiques) pour la prise de décision.

### 2.3 Objectifs Académiques
Le projet a pour but de valider les compétences acquises durant notre formation en concevant un système de A à Z (Full-Stack). La complexité a été sciemment maîtrisée pour rester cohérente avec la durée d'un stage de fin d'études de 3 mois, en évitant les surcouches logicielles non nécessaires à ce stade (microservices lourds, architectures d'entreprises complexes).

### 2.4 Résultats Attendus
L'obtention d'un prototype fonctionnel, facile à déployer, capable de générer ses propres données de simulation, de les analyser par IA et de les afficher via une interface de type "Mode Clair" adaptée aux présentations et à un usage prolongé.

---

## 3. ARCHITECTURE TECHNIQUE

La plateforme repose sur une architecture moderne de type client/serveur, structurée en plusieurs modules interdépendants.

- **Frontend (React.js)** : Responsable de l'Interface Utilisateur (UI). Il communique avec le Backend via des requêtes HTTP (API REST) et gère l'affichage dynamique (tableaux, cartes, graphiques).
- **Backend (Node.js + Express / Python Flask)** : Gère la logique métier, la génération des données simulées, et expose les points d'accès (endpoints) pour le Frontend.
- **Base de Données (PostgreSQL)** : Assure la persistance des données. Elle stocke l'inventaire des antennes, l'historique des mesures, les anomalies détectées et les rapports d'incidents.
- **Module IA (Python + Scikit-Learn - Isolation Forest)** : Un service analytique dédié à la détection d'anomalies.
- **Déploiement (Docker Compose)** : L'ensemble des services est conteneurisé. Docker permet d'encapsuler chaque brique (Base de données, API, Frontend) pour assurer une portabilité totale et simplifier l'installation.

L'ensemble de ces briques communique de manière fluide : le Frontend interroge le Backend via l'API, le Backend dialogue avec PostgreSQL pour la lecture/écriture, et le conteneur IA exécute ses scripts d'analyse sur les données de la base avant d'y inscrire les résultats (incidents).

---

## 4. CONCEPTION DE LA BASE DE DONNÉES

Le système s'appuie sur le Système de Gestion de Base de Données Relationnelle (SGBDR) **PostgreSQL**, choisi pour sa robustesse, sa forte intégrité des données et sa capacité à gérer des volumes importants de séries temporelles avec une grande fiabilité.

### 4.1 Tables Principales
- **`antennes`** : Stocke l'inventaire des équipements physiques.
  - *Champs importants* : `id`, `nom`, `latitude`, `longitude`, `type` (4G/5G), `zone`, `statut`.
- **`mesures`** : Contient l'historique des indicateurs de performance générés.
  - *Champs importants* : `id`, `antenne_id` (clé étrangère), `date_mesure`, `rssi`, `latency`, `packet_loss`, `cpu`, `temperature`, `bandwidth`.
- **`anomalies`** : Enregistre les détections isolées par l'algorithme d'IA.
  - *Champs importants* : `id`, `mesure_id` (clé étrangère), `date_detection`, `score`, `description`.
- **`incidents`** / **`alertes`** : Représente les événements critiques générés suite aux anomalies ou à des pannes majeures, nécessitant l'intervention d'un opérateur.
  - *Champs importants* : `id`, `antenne_id`, `niveau_gravite`, `statut` (En cours, Résolu), `date_ouverture`.

Cette modélisation en étoile (autour des antennes) permet d'optimiser les requêtes pour l'affichage de l'historique d'un équipement spécifique ou l'analyse globale du réseau à un instant T.

---

## 5. PAGE DASHBOARD (TABLEAU DE BORD)

Le Dashboard est la page d'accueil et le centre névralgique de la plateforme.

- **Rôle** : Offrir une vue d'ensemble macroscopique de l'état du réseau en un seul coup d'œil.
- **KPIs Affichés** : Nombre total d'antennes, Taux de disponibilité global (%), Nombre d'alertes actives, et Incidents critiques.
- **Calcul de Disponibilité** : Ce pourcentage est calculé dynamiquement en soustrayant le nombre d'antennes "hors service" ou "en alerte critique" au parc total.
- **AI Risk Score & Confiance du Modèle** : Affiche un score global de santé généré par l'IA, ainsi que le taux de confiance du modèle basé sur le volume de données analysé.
- **Simplicité** : Le dashboard est volontairement épuré pour éviter la surcharge cognitive (Information Overload) très commune dans les anciens systèmes NOC.

---

## 6. PAGE DE CARTOGRAPHIE RÉSEAU (MAP)

La visualisation spatiale est essentielle pour identifier des problèmes régionaux (ex: coupure de courant dans une zone spécifique).

- **Visualisation Géographique** : La carte place l'intégralité des antennes avec des marqueurs dynamiques.
- **Clustering** : Pour éviter l'encombrement visuel et maintenir des performances fluides, les antennes proches sont regroupées géographiquement (clusters).
- **Marqueurs & Couleurs** : Chaque marqueur reflète l'état de l'antenne (Vert = Normal, Orange = Alerte, Rouge = Critique). Les antennes en état critique bénéficient d'une animation "pulsante" (pulse) pour attirer rapidement l'attention de l'opérateur.
- **Technologie** : Utilisation de la librairie **React-Leaflet** avec une base cartographique *CartoDB Light*, choisie pour offrir un contraste visuel optimal avec le thème clair de l'application et faire ressortir les alertes.

---

## 7. PAGE DES ÉQUIPEMENTS (ANTENNES)

Cette interface agit comme l'inventaire technique détaillé du matériel.

- **Rôle** : Permet de consulter l'état précis de chaque équipement et de filtrer facilement le parc par zone, type (4G/5G) ou statut de fonctionnement.
- **KPIs Télécoms affichés** :
  - **RSSI** (Signal Strength) : Puissance du signal reçu.
  - **Latence (Ping)** : Temps de réponse de l'antenne.
  - **Packet Loss** : Taux de perte de paquets.
  - **Charge CPU & Température** : Indicateurs matériels pour prévenir les pannes physiques (surchauffe).
  - **Bande Passante (Bandwidth)** : Capacité de trafic actuelle.
- **Logique Télécom Réaliste** : Ces données sont simulées mais générées de manière à respecter les plages de valeurs physiques cohérentes avec le monde des télécoms (ex: Latence acceptable entre 10ms et 50ms, alarmante au-delà de 150ms).

---

## 8. PAGE DE DÉTECTION IA (ANALYTICS)

La page d'Analytique est dédiée à l'explication et à la visualisation du travail du module d'Intelligence Artificielle.

- **Algorithme Choisi : Isolation Forest**
  L'Isolation Forest est un algorithme de détection d'anomalies de type non supervisé.
- **Pourquoi l'Isolation Forest ?**
  - **Simplicité et Légèreté** : Contrairement aux réseaux de neurones complexes, il s'exécute très rapidement et nécessite peu de ressources de calcul, ce qui correspond idéalement à la taille de notre dataset.
  - **Parfait pour les anomalies** : Il est spécifiquement conçu pour "isoler" les points de données aberrants (les pannes) plutôt que de modéliser ce qui est normal.
  - **Clarté et Explicabilité** : Idéal pour une soutenance académique (PFE), son fonctionnement est aisé à argumenter. Le modèle attribue un "score d'anomalie" direct à chaque mesure.
- **Logique de Détection** : L'algorithme scanne l'ensemble des métriques d'une antenne (combinaison de température, latence, packet loss). Si un comportement dévie drastiquement du comportement global des autres équipements, l'antenne est flaggée avec un score d'anomalie élevé.
- **Workflow d'Analyse** : Les anomalies détectées et présentées sur cette page constituent la base de génération automatique des alertes visibles sur le Dashboard.

---

## 9. PAGE DE MODÉRATION

La détection IA, bien que puissante, n'est jamais infaillible. Le concept même du NOC implique toujours une validation humaine experte (approche *Human-in-the-loop*).

- **Rôle du Modérateur** : Visualiser les anomalies détectées par l'IA et les pannes matérielles confirmées.
- **Gestion des Alertes** : L'opérateur peut analyser les détails de l'incident, décider de déployer une équipe technique sur le terrain, puis "Résoudre" et clôturer l'alerte depuis l'interface une fois l'antenne réparée.
- **Workflow de Vérification** : Assure que le système logiciel ne prend pas de décisions critiques de manière totalement automatisée sans supervision humaine (une bonne pratique en ingénierie de production).

---

## 10. PAGE DES RAPPORTS

La génération de rapports est cruciale pour le suivi de la qualité de service et le reporting managérial.

- **Génération de Rapports** : Permet aux chefs de projet et ingénieurs réseau d'exporter un cliché de l'état de l'infrastructure à l'instant T.
- **Formats d'Export** :
  - **PDF** : Synthèse propre et visuelle de l'état du réseau (incidents, KPIs), idéale pour les réunions de direction et le reporting exécutif.
  - **Excel / CSV** : Export tabulaire brut de l'historique pour des post-analyses approfondies (par exemple pour l'équipe Data Science).
- **Workflow d'Exportation** : Le frontend (React) envoie une requête API au Backend. Le Backend interroge la base PostgreSQL, traite la donnée (via des librairies dédiées), génère le fichier côté serveur, et renvoie un Blob (fichier binaire) qui déclenche immédiatement le téléchargement sur le navigateur du client.

---

## 11. SIMULATION DES DONNÉES TÉLÉCOMS

Puisque nous n'avons pas d'accès direct au réseau physique de production d'un opérateur (données sensibles et confidentielles), un pipeline de simulation robuste et réaliste a été mis en place.

- **Le Parc** : Simulation de 120 antennes réparties sur la côte est (Mahdia, Sousse, Monastir).
- **Cycle de Génération** : Un script Python automatisé s'exécute en arrière-plan toutes les 30 minutes.
- **Génération Réaliste** : Le script ne génère pas de simples nombres aléatoires uniformes. Il utilise une logique pour simuler des fluctuations normales, et induit de manière probabiliste des "pics" (pertes de paquets intenses, chute de bande passante, surchauffe CPU) sur un faible pourcentage d'antennes pour simuler de vraies pannes qui devront être détectées par l'IA.

---

## 12. LE WORKFLOW COMPLET DE L'IA

L'intégration de l'IA et de la Data dans la plateforme s'articule autour d'un pipeline clair :

1. **Génération (Simulation)** : Le système crée et collecte les mesures télécoms périodiquement.
2. **Stockage** : Insertion en base de données (PostgreSQL) pour persistance.
3. **Analyse IA (Isolation Forest)** : Le modèle Python est déclenché sur les données les plus récentes. Il évalue et attribue un score d'anomalie pour chaque ligne.
4. **Détection** : Les mesures présentant un score aberrant sont formellement identifiées comme des anomalies.
5. **Création d'Incidents** : Le Backend qualifie ces anomalies et génère des tickets d'incidents.
6. **Mise à jour (Frontend)** : Le Dashboard (React) récupère ces nouvelles alertes et met à jour instantanément les indicateurs (Compteurs d'alertes, AI Risk Score, Disponibilité).
7. **Modération** : Un opérateur NOC évalue, traite et résout l'incident depuis l'interface.

---

## 13. GÉNÉRATION DU RAPPORT PDF (LOGIQUE DÉTAILLÉE)

La création de documents PDF démontre la capacité du système à formater des données techniques en informations "Business" lisibles.

- **Frontend** : L'utilisateur clique sur le bouton "Exporter en PDF". Une requête HTTP GET est déclenchée.
- **Backend (API)** : Le serveur rassemble les informations via des requêtes SQL avancées (`COUNT`, `GROUP BY`, agrégations) pour récupérer les KPIs globaux et les incidents actifs.
- **Génération** : Le document PDF est dessiné programmatiquement en mémoire (ajout d'en-têtes, mise en forme des tableaux, textes structurés).
- **Livraison** : Le Buffer généré est transmis vers le client via des en-têtes HTTP de téléchargement (`Content-Disposition: attachment`), déclenchant la sauvegarde locale fluide et immédiate.

---

## 14. DÉPLOIEMENT VIA DOCKER

Pour garantir un rendu professionnel et simplifier la livraison et la présentation de ce projet académique, la plateforme entière a été packagée grâce à **Docker** et **Docker Compose**.

- **L'Architecture Conteneurisée** :
  - Un conteneur pour le **Frontend** (React).
  - Un conteneur pour le **Backend** (API Express / Node).
  - Un conteneur pour la **Base de Données** (PostgreSQL).
  - Un conteneur pour le **Moteur de Simulation & IA** (Python).
- **Les Avantages Majeurs** :
  - **Portabilité** : Élimine le problème classique du "Ça marche sur ma machine". Le projet fonctionnera à l'identique sur n'importe quel ordinateur équipé de Docker.
  - **Déploiement Facilité** : Une unique commande (`docker compose up`) suffit à monter l'ensemble du réseau interne, initialiser la base de données, démarrer les serveurs et l'IA en quelques secondes.
  - **Reproductibilité Académique** : Permet de présenter et de défendre le projet sereinement lors de la soutenance sans craindre de conflits de dépendances locales.

---

## 15. SÉCURITÉ ET LIMITES DU PROJET

### 15.1 Sécurité de Base
Le système implémente une validation stricte des requêtes au niveau de l'API afin de prévenir des failles courantes comme les injections SQL. L'accès à la base de données PostgreSQL est restreint par une authentification par mot de passe et protégé via l'isolation réseau interne native de Docker.

### 15.2 Limites Académiques
Le projet a été dimensionné pour démontrer une faisabilité technique de A à Z en un temps limité (stage de 3 mois). Il comporte donc des limites inhérentes :
- **Données Simulées** : Les métriques générées, bien que logiques, ne capturent pas l'entièreté du chaos ou du bruit d'un véritable réseau télécom de production.
- **Scalabilité (Mise à l'échelle)** : La base PostgreSQL centralisée est largement suffisante et optimale pour 120 antennes, mais le monitoring temps réel d'un parc national (ex: 20 000 antennes) nécessiterait le pivotement vers une architecture Big Data distribuée (comme Apache Kafka associé à TimescaleDB).
- **Modèle IA Simplifié** : L'Isolation Forest fonctionne sur un principe "Batch" périodique et ne ré-apprend pas continuellement des retours du modérateur (absence de Continuous Learning).

---

## 16. PERSPECTIVES ET AMÉLIORATIONS FUTURES

Si le prototype devait évoluer vers un produit commercial ou industriel complet, voici les axes d'amélioration prioritaires :

- **Connectivité Physique Réelle** : Remplacer le pipeline de simulation par la collecte de véritables métriques matérielles via des agents SNMP ou par l'interrogation directe des API constructeurs (Nokia, Huawei, Ericsson).
- **Maintenance Prédictive Avancée** : Passer de la simple détection d'anomalie post-panne à de la véritable prédiction de séries temporelles (Deep Learning : LSTM ou Prophet) pour anticiper les défaillances plusieurs jours avant qu'elles ne surviennent.
- **Système d'Alerte Push Actif** : Intégration d'un module d'envoi automatique de SMS (via Twilio) ou d'emails directement aux techniciens terrain dès la confirmation d'un incident critique par le système.

---

## 17. INTÉGRATION SIG : GEOSERVER ET GEONETWORK

### 17.1 Contexte et Motivation
Les systèmes d'information géographique (SIG) constituent un outil fondamental dans la supervision des infrastructures télécom. La localisation précise des antennes, la visualisation des zones d'anomalies et la gestion des métadonnées géospatiales apportent une dimension analytique supplémentaire au-delà des simples tableaux de KPIs. Cette section documente l'intégration de deux standards du monde SIG open source : **GeoServer** et **GeoNetwork**.

### 17.2 Architecture GIS Adoptée
L'architecture GIS retenue est volontairement simple et directement intégrable à l'infrastructure Docker existante :

- **PostgreSQL/PostGIS** (déjà en place) → stocke les géométries des antennes (`geometry(Point, 4326)`)
- **GeoServer** → lit ces données PostGIS et les publie en tant que services standardisés (WMS/WFS)
- **React Leaflet** (frontend) → consomme ces services WMS comme couches cartographiques superposées
- **GeoNetwork** → catalogue les métadonnées de chaque couche géographique

### 17.3 GeoServer — Serveur de Publication Géographique
GeoServer est un serveur open source conforme aux standards OGC (*Open Geospatial Consortium*) qui permet de publier des données spatiales sous différents formats interopérables.

**Rôle dans le projet** :
- Connecté directement à notre base **PostgreSQL/PostGIS** via un *DataStore*
- Publie deux couches télécom principales :
  - `antennes_geo` : l'inventaire complet des antennes avec leur géométrie et statut
  - `antennes_statut` : la vue temps réel (dernière mesure par antenne, CPU, température, disponibilité)
- Expose ces couches via les services standardisés **WMS** (Web Map Service) et **WFS** (Web Feature Service)

**Avantage pédagogique** : L'utilisation de GeoServer démontre la maîtrise des standards géospatiaux OGC, compétence valorisée dans les profils ingénieurs télécoms et SIG.

### 17.4 Intégration Frontend — WMS dans React Leaflet
La page de cartographie React intègre les couches WMS de GeoServer grâce au composant `WMSTileLayer` de la librairie `react-leaflet`.

Le système est conçu en mode **dégradé gracieux** (*graceful degradation*) :
1. Au chargement, le frontend vérifie silencieusement si GeoServer est joignable
2. Si **actif** → deux couches WMS apparaissent dans le contrôleur de couches (en haut à droite de la carte), activables/désactivables librement
3. Si **hors ligne** → la carte continue de fonctionner normalement avec les marqueurs Leaflet issus de l'API Flask

Un badge dynamique **"GeoServer WMS — Actif / Hors ligne"** est affiché dans la légende de la carte pour informer l'opérateur de l'état du service.

### 17.5 GeoNetwork — Catalogue de Métadonnées
GeoNetwork est un catalogue de métadonnées géospatiales conforme au standard **ISO 19115** et au protocole **OGC CSW** (*Catalogue Service for the Web*).

**Rôle dans le projet** :
- Référencer et décrire officiellement chaque couche géographique télécom
- Permettre la découverte des données via le protocole standardisé CSW
- Documenter la provenance, la fréquence de mise à jour, la couverture géographique et les droits d'usage de chaque jeu de données

**Fiches de métadonnées créées** :
1. *"Antennes Télécom 4G/5G — Gouvernorat de Mahdia"* → décrit la couche `antennes_geo`
2. *"Statut Temps Réel des Antennes — Vue NOC"* → décrit la couche `antennes_statut`

Chaque fiche intègre l'emprise géographique (bounding box), les mots-clés techniques, la fréquence de mise à jour, et un lien direct vers le service WMS correspondant dans GeoServer.

### 17.6 Workflow GIS Complet
Le pipeline SIG s'articule autour des étapes suivantes :

1. **Stockage** : Les coordonnées des antennes sont stockées en PostGIS sous forme de géométries `POINT` (SRID 4326/WGS84)
2. **Publication** : GeoServer interroge PostGIS et expose les vues sous forme de services WMS/WFS
3. **Visualisation** : React Leaflet charge ces couches WMS et les superpose à la carte de base CartoDB
4. **Documentation** : GeoNetwork référence les couches et leurs métadonnées dans un catalogue CSW interopérable
5. **Mise à jour automatique** : Chaque cycle de simulation (30 min) met à jour la base PostGIS, ce qui se répercute automatiquement dans les couches GeoServer sans intervention manuelle

### 17.7 Déploiement Docker
Les deux services GIS sont ajoutés au `docker-compose.yml` existant :

```yaml
geoserver:
  image: docker.osgeo.org/geoserver:2.25.2
  ports: ["8080:8080"]

geonetwork:
  image: geonetwork:4.2.7
  ports: ["8081:8080"]
```

La configuration initiale de GeoServer (création du workspace, du datastore et publication des couches) est automatisée via le script Python `geoserver_setup.py`. La création des métadonnées GeoNetwork est automatisée via `geonetwork_metadata.py`.

---

## 18. CONCLUSION

Ce Projet de Fin d'Études a abouti avec succès à la création d'une **Plateforme de Supervision NOC Intelligente**. Les objectifs fixés initialement ont été pleinement atteints : de la conception de la base de données relationnelle jusqu'à la restitution graphique (UI/UX), en passant par l'intégration d'une brique d'Intelligence Artificielle fonctionnelle.

L'apport de l'IA (Isolation Forest) au sein de la plateforme démontre qu'il est possible de soulager significativement le travail fastidieux des opérateurs réseau. En filtrant automatiquement le "bruit" des fausses alertes et en isolant intelligemment les comportements anormaux, le système permet aux équipes techniques de se concentrer sur la résolution effective des incidents plutôt que sur leur recherche fastidieuse.

Ce projet prouve de manière académique et pragmatique la faisabilité de la modernisation des outils d'exploitation télécoms classiques en alliant le développement logiciel Full-Stack moderne, l'architecture conteneurisée et la Data Science.
