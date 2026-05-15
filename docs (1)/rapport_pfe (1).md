# Rapport de Projet de Fin d'Études
## Plateforme SIG de Supervision Réseau Télécom avec Analyse Prédictive

**Établissement :** Institut Supérieur d'Informatique et des Techniques de Communication (ISITCom)  
**Entreprise d'accueil :** Tunisie Telecom — Direction Régionale de Mahdia  
**Filière :** Licence en Génie Informatique  
**Année universitaire :** 2025–2026  
**Encadrant académique :** [Nom de l'encadrant]  
**Encadrant professionnel :** [Nom de l'encadrant TT]  
**Étudiant :** Malek

---

## Table des matières

- [Introduction générale](#introduction-générale)
- [Chapitre 1 : Présentation générale](#chapitre-1--présentation-générale)
- [Chapitre 2 : Préparation du projet](#chapitre-2--préparation-du-projet)
- [Chapitre 3 : Sprint 1 – Infrastructure et GeoNetwork](#chapitre-3--sprint-1)
- [Chapitre 4 : Sprint 2 – API Flask et données géographiques](#chapitre-4--sprint-2)
- [Chapitre 5 : Sprint 3 – Supervision et visualisation](#chapitre-5--sprint-3)
- [Chapitre 6 : Sprint 4 – Analyse prédictive et alertes intelligentes](#chapitre-6--sprint-4)
- [Chapitre 7 : Tests, validation et difficultés](#chapitre-7--tests-validation-et-difficultés)
- [Conclusion générale](#conclusion-générale)

---

## Introduction générale

Dans un monde de plus en plus connecté, les infrastructures de télécommunications jouent un rôle fondamental dans le développement économique et social des régions. La gestion efficace de ces infrastructures représente un défi majeur pour les opérateurs télécoms, en particulier lorsqu'il s'agit de superviser des centaines d'équipements répartis géographiquement sur un territoire donné.

Tunisie Telecom, premier opérateur historique de la télécommunication en Tunisie, gère un réseau national d'antennes, de stations de base et d'équipements critiques. Sa direction régionale de Mahdia, comme toutes les directions régionales, fait face à la problématique de la supervision en temps réel de ses équipements télécom, de la détection préventive des pannes, et de la prise de décision rapide en cas d'incident.

Le présent projet de fin d'études s'inscrit dans ce contexte et propose le développement d'une **Plateforme SIG (Système d'Information Géographique) de supervision réseau** intégrée, alliant la visualisation cartographique interactive, la supervision temps réel, et l'analyse prédictive par intelligence artificielle.

La solution développée repose sur une architecture moderne entièrement conteneurisée avec Docker, combinant :
- Une base de données géospatiale **PostgreSQL/PostGIS**
- Un serveur cartographique **GeoServer** pour la publication WMS
- Un catalogue de métadonnées **GeoNetwork**
- Une API REST développée avec **Flask (Python)**
- Un module d'apprentissage automatique avec **Isolation Forest (Scikit-Learn)**
- Un tableau de bord interactif développé avec **React.js** et **Leaflet.js**
- Un système de monitoring avec **Grafana**

Ce rapport décrit l'ensemble du cycle de développement de cette plateforme, organisé selon la méthodologie agile Scrum en quatre sprints, depuis la conception de l'architecture jusqu'à la validation finale.

---

# Chapitre 1 : Présentation générale

## Introduction

Ce premier chapitre présente le cadre général du projet de fin d'études. Nous introduisons l'organisme d'accueil, le contexte et la problématique qui ont motivé le développement de la plateforme SIG, ainsi que la méthodologie de travail adoptée tout au long du projet.

---

## 1.1 Présentation de l'organisme d'accueil

### 1.1.1 Présentation de Tunisie Telecom

Tunisie Telecom (TT) est l'opérateur historique des télécommunications en Tunisie. Fondée en 1995 sous la forme d'une société anonyme suite à la restructuration de l'Office National des Télécommunications (ONT), l'entreprise est aujourd'hui l'un des acteurs majeurs du secteur des TIC (Technologies de l'Information et de la Communication) en Afrique du Nord.

**Fiche signalétique :**

| Critère | Information |
|---|---|
| Raison sociale | Tunisie Telecom |
| Forme juridique | Société Anonyme (SA) |
| Capital social | 1 500 000 000 DT |
| Siège social | 13, Avenue Jugurtha, Mutuelleville, Tunis 1002 |
| Fondation | 1995 |
| Direction régionale | Mahdia |
| Secteur | Télécommunications |
| Effectif | ~6 000 employés |
| Site web | www.tunisietelecom.tn |

Tunisie Telecom propose une gamme complète de services : téléphonie fixe, téléphonie mobile (2G/3G/4G/5G en cours de déploiement), accès Internet haut débit (ADSL, Fibre optique), et services aux entreprises (VPN, cloud, datacenter).

### 1.1.2 Secteur d'activité

Le secteur des télécommunications en Tunisie est régi par l'Instance Nationale des Télécommunications (INT). Tunisie Telecom opère dans ce secteur concurrentiel face à d'autres opérateurs comme Ooredoo Tunisie et Orange Tunisie.

Les principaux domaines d'activité de Tunisie Telecom sont :

- **Téléphonie fixe** : réseau cuivre couvrant l'ensemble du territoire national
- **Téléphonie mobile** : plus de 6 millions d'abonnés avec couverture nationale 4G
- **Internet haut débit** : services ADSL et FTTH (Fiber To The Home)
- **Services entreprises** : solutions B2B incluant VPN MPLS, hébergement, cybersécurité
- **Téléphonie IP (VoIP)** : infrastructure NGN (Next Generation Network)

La direction régionale de **Mahdia** supervise l'ensemble des équipements de télécommunications du gouvernorat de Mahdia, couvrant une superficie d'environ 2 966 km² avec une population de plus de 400 000 habitants.

### 1.1.3 Missions et contexte du stage

Le stage de fin d'études s'est déroulé au sein de la **Direction Régionale de Mahdia** de Tunisie Telecom, dans le département technique chargé de la supervision et de la maintenance du réseau.

**Durée du stage :** 4 mois (Février – Mai 2026)

**Missions principales :**
- Analyse de l'infrastructure réseau existante
- Conception et développement d'une plateforme SIG de supervision
- Intégration de l'intelligence artificielle pour la détection d'anomalies
- Déploiement de la solution en environnement Docker
- Formation et documentation technique

---

## 1.2 Cadre du projet

### 1.2.1 Contexte du projet

Le gouvernorat de Mahdia dispose d'un réseau dense d'équipements télécom : antennes relais (BTS/NodeB/eNodeB), centraux téléphoniques, nœuds de transmission et équipements de supervision. Ces équipements sont répartis sur l'ensemble du territoire et génèrent en permanence des données de performance (température, charge CPU, qualité du signal, trafic réseau).

La supervision de ces équipements est aujourd'hui réalisée de manière fragmentée, sans vision géographique unifiée ni capacité prédictive. Les équipes techniques interviennent souvent en mode curatif (après la panne) plutôt qu'en mode préventif.

### 1.2.2 Problématique de la supervision réseau

La supervision réseau dans les directions régionales de Tunisie Telecom souffre de plusieurs lacunes :

**Problèmes identifiés :**

1. **Absence de visualisation géographique** : Les équipements ne sont pas positionnés sur une carte interactive. Les techniciens ne disposent pas d'une vue SIG permettant de localiser rapidement les incidents.

2. **Supervision réactive** : Les pannes sont détectées après signalement des clients ou après intervention sur site. Il n'existe pas de système de détection préventive.

3. **Données fragmentées** : Les données de performance sont stockées dans des systèmes hétérogènes (fichiers Excel, bases locales) sans consolidation centrale.

4. **Manque d'analyse prédictive** : Aucun outil d'intelligence artificielle n'est utilisé pour anticiper les défaillances d'équipements.

5. **Interface vieillissante** : Les outils de supervision existants offrent des interfaces non adaptées aux exigences modernes de visualisation et d'ergonomie.

### 1.2.3 Besoin de centralisation et d'analyse prédictive

Face à ces lacunes, la direction régionale de Mahdia exprime le besoin d'une solution centralisée permettant :

- La **visualisation cartographique** en temps réel de tous les équipements réseau
- La **supervision continue** des métriques de performance (température, CPU, signal)
- La **détection automatique des anomalies** par algorithmes d'apprentissage automatique
- La **génération d'alertes intelligentes** priorisées par niveau de criticité
- L'**historisation des données** pour des analyses tendancielles
- Un **tableau de bord unifié** accessible depuis tout poste de travail

### 1.2.4 Analyse et critique de l'existant

L'analyse de l'existant a permis d'identifier les forces et faiblesses du système actuel :

**Forces de l'existant :**
- Existence d'une base de données partielle des équipements
- Connaissance terrain des techniciens expérimentés
- Infrastructure réseau bien documentée

**Faiblesses de l'existant :**
- Aucune interface cartographique SIG
- Supervision manuelle et non centralisée
- Absence totale d'IA ou d'analyse prédictive
- Temps de réaction aux incidents trop long (moyenne > 2h)
- Aucune API standardisée pour l'accès aux données

**Opportunités :**
- Technologies open source matures (PostGIS, GeoServer, React.js)
- Écosystème Docker facilitant le déploiement
- Algorithmes ML accessibles via Scikit-Learn

### 1.2.5 Solution proposée

La solution proposée est une **Plateforme SIG intégrée de supervision réseau** nommée **GEO-TÉLÉCOM**, composée des modules suivants :

```
┌─────────────────────────────────────────────────────────┐
│              PLATEFORME GEO-TÉLÉCOM                     │
├──────────────┬──────────────┬───────────────────────────┤
│   Module SIG  │  Module API  │  Module IA                │
│  (GeoServer + │  (Flask REST)│  (Isolation Forest)       │
│   GeoNetwork) │              │                           │
├──────────────┴──────────────┴───────────────────────────┤
│              Base de données PostgreSQL/PostGIS          │
├─────────────────────────────────────────────────────────┤
│         Dashboard React.js + Grafana                     │
└─────────────────────────────────────────────────────────┘
```

---

## 1.3 Méthodologies de travail

### 1.3.1 Méthodologies agiles

Les méthodologies agiles constituent un ensemble de pratiques de gestion de projet qui privilégient la flexibilité, la collaboration et la livraison incrémentale de valeur. Elles s'opposent aux approches traditionnelles dites "en cascade" (Waterfall) où toutes les phases sont planifiées en amont.

Les principes fondamentaux des méthodes agiles, tels que définis par le **Manifeste Agile (2001)**, sont :
- Individus et interactions plutôt que processus et outils
- Logiciel fonctionnel plutôt que documentation exhaustive
- Collaboration avec le client plutôt que négociation contractuelle
- Réponse au changement plutôt que suivi d'un plan

### 1.3.2 Méthodologie Scrum

**Scrum** est le cadre agile le plus utilisé dans l'industrie du logiciel. Il organise le travail en itérations courtes appelées **Sprints** (généralement de 2 à 4 semaines), à l'issue desquelles un incrément fonctionnel du produit est livré.

**Les rôles Scrum :**

| Rôle | Responsabilité | Dans notre projet |
|---|---|---|
| Product Owner | Définit les priorités et le backlog | Encadrant professionnel TT |
| Scrum Master | Facilite les réunions et lève les obstacles | Étudiant (auto-géré) |
| Équipe de développement | Réalise les fonctionnalités | Étudiant stagiaire |

**Les cérémonies Scrum :**
- **Sprint Planning** : Planification des tâches du sprint
- **Daily Scrum** : Point quotidien de 15 minutes (adapté en hebdomadaire pour le stage)
- **Sprint Review** : Démonstration de l'incrément produit
- **Sprint Retrospective** : Analyse des améliorations de processus

**Choix de Scrum pour ce projet :**

Scrum a été retenu pour ce projet pour plusieurs raisons :
1. Les exigences évoluent progressivement au fil des découvertes techniques
2. Des livraisons intermédiaires sont nécessaires pour validation par l'encadrant TT
3. La durée du stage (4 mois) se prête naturellement à 4 sprints de 3-4 semaines
4. La méthodologie favorise l'adaptation rapide aux contraintes techniques rencontrées

**Organisation des sprints du projet :**

| Sprint | Durée | Objectif principal |
|---|---|---|
| Sprint 1 | 3 semaines | Infrastructure Docker + GeoNetwork + PostgreSQL |
| Sprint 2 | 3 semaines | API Flask + Services REST + Exploitation GeoNetwork |
| Sprint 3 | 4 semaines | Dashboard React + Grafana + Visualisation cartographique |
| Sprint 4 | 3 semaines | IA Isolation Forest + Alertes intelligentes |

---

## Conclusion

Ce premier chapitre a permis de situer le projet dans son contexte organisationnel et technique. Nous avons présenté Tunisie Telecom et sa direction régionale de Mahdia, exposé la problématique de supervision réseau, et justifié le choix de la méthodologie Scrum pour conduire le développement. Le chapitre suivant détaille la préparation du projet : capture du besoin, architecture globale, et planification des sprints.

---

# Chapitre 2 : Préparation du projet

## Introduction

Ce deuxième chapitre est consacré à la phase de conception et de préparation de notre projet. Nous y détaillons l'analyse des besoins, la modélisation à travers les diagrammes de cas d'utilisation, ainsi que l'environnement technique et l'architecture globale de la solution GEO-TÉLÉCOM.

---

## 2.1 Capture du besoin

### 2.1.1 Spécification des besoins

La phase de spécification consiste à identifier précisément ce que le système doit faire et quelles sont les contraintes à respecter.

#### 2.1.1.1 Besoins fonctionnels

Les besoins fonctionnels décrivent les actions que le système doit être capable de réaliser :

- **Gestion des équipements** : Consulter la liste exhaustive des antennes et équipements réseau.
- **Visualisation SIG** : Afficher les équipements sur une carte interactive (Leaflet) avec des fonds de carte variés.
- **Supervision en temps réel** : Suivre l'évolution des métriques (Température, CPU) toutes les 60 secondes.
- **Analyse prédictive** : Détecter automatiquement les anomalies de comportement via l'IA.
- **Système d'alerte** : Identifier visuellement les zones et équipements en état critique ou d'alerte.
- **Consultation des métadonnées** : Accéder aux informations détaillées via GeoNetwork.

#### 2.1.1.2 Besoins non fonctionnels

Les besoins non fonctionnels concernent les qualités du système :

- **Performance** : Temps de réponse rapide de l'API et fluidité de la carte.
- **Disponibilité** : Système accessible 24h/24 via l'infrastructure Docker.
- **Sécurité** : Intégrité des données géospatiales dans PostgreSQL.
- **Portabilité** : Utilisation de conteneurs Docker pour garantir le fonctionnement sur n'importe quel serveur.
- **Ergonomie** : Interface moderne (Glassmorphism), sombre et intuitive pour les opérateurs.

### 2.1.2 Modélisation du besoin

#### 2.1.2.1 Identification des acteurs

- **Administrateur Réseau** : Gère l'infrastructure, les configurations GeoServer et les accès.
- **Technicien de Supervision** : Consulte le dashboard, suit les alertes et analyse les recommandations de l'IA.
- **Système (IA)** : Génère les prédictions et identifie les anomalies.

#### 2.1.2.2 Diagramme de cas d'utilisation global

Le diagramme global présente les interactions principales. (Note : Les diagrammes visuels sont à inclure dans la version finale du document Word).

---

## 2.2 Pilotage du projet avec Scrum

### 2.2.1 Équipe et rôles

- **Malek (Étudiant)** : Développeur Full-Stack, Data Scientist et Scrum Master.
- **Encadrant TT** : Product Owner, validateur des fonctionnalités.

### 2.2.3 Backlog du produit

Le Backlog regroupe l'ensemble des "User Stories" (US) identifiées :
1. En tant que technicien, je veux voir les antennes sur une carte pour les localiser.
2. En tant qu'administrateur, je veux consulter les statistiques globales du réseau.
3. En tant que technicien, je veux être alerté quand une antenne surchauffe.
4. En tant qu'analyste, je veux que l'IA détecte les pannes avant qu'elles ne surviennent.

### 2.2.3 Planification des Sprints

Le projet est découpé en 4 Sprints majeurs, chacun produisant un incrément testable de la plateforme.

---

## 2.3 Environnement de travail

### 2.3.1 Environnement matériel

- **Machine de développement** : PC Portable (Intel i7, 16GB RAM).
- **Serveur de déploiement** : Serveur Windows/Linux supportant Docker.

### 2.3.2 Environnement logiciel

- **OS** : Windows / Linux.
- **Langages** : Python (Flask), JavaScript (React), SQL, HTML/CSS.
- **Outils** : VS Code, Docker Desktop, pgAdmin.

---

## Architecture globale

### Schéma d’architecture :
L'architecture est de type n-tiers, basée sur des micro-services conteneurisés.

### Flux de données :
1. Les capteurs simulent des données vers la base **PostgreSQL**.
2. **GeoServer** lit les données spatiales pour générer les flux WMS.
3. L'**API Flask** traite les données et exécute le modèle IA.
4. Le **Frontend React** consomme l'API et affiche la carte Leaflet.

### Vue en conteneurs (Docker) :
- `react_app` : Frontend.
- `flask_api` : Backend Logic/IA.
- `postgres` : Base de données PostGIS.
- `geoserver` : Serveur cartographique.
- `geonetwork` : Catalogue de métadonnées.

---

## Conclusion

Ce chapitre a posé les bases conceptuelles et techniques du projet. Avec une architecture solide et des besoins clairement définis, nous pouvons maintenant entamer la phase de réalisation technique à travers le premier sprint.

---

# Chapitre 3 : SPRINT 1 – Mise en place de l’infrastructure et intégration de GeoNetwork

## Introduction

Le premier sprint constitue la fondation technique de la plateforme. Il s'agit de mettre en place l'environnement de virtualisation avec Docker, de configurer la base de données PostGIS et d'intégrer le catalogue GeoNetwork pour la gestion des métadonnées.

---

### ➢ Objectifs du Sprint 1
- Initialiser le dépôt de code et la structure du projet.
- Configurer le fichier `docker-compose.yml` pour orchestrer les services.
- Déployer PostgreSQL avec l'extension PostGIS.
- Mettre en service GeoNetwork et importer les premières couches de métadonnées.

### ➢ Positionnement du sprint dans le projet
Ce sprint se situe au tout début de la phase de réalisation (Semaines 1-3). Il permet de valider la connectivité entre les différents conteneurs.

---

## 3.1 Backlog du Sprint 1

Le backlog de ce sprint est composé des tâches techniques suivantes :
- **Installation et configuration de Docker** : Préparation des images de base.
- **Déploiement de GeoNetwork** : Configuration du service sur le port 8080.
- **Configuration de PostgreSQL** : Création de la base `antennes_mahdia` et des utilisateurs.
- **Intégration des données géographiques** : Création des tables spatiales et import des coordonnées des antennes.

---

## 3.2 Analyse

### 3.2.1 Diagramme de cas d’utilisation
Le sprint se concentre sur les cas d'utilisation liés à l'administration des données.

### 3.2.2 Description du cas d’utilisation : Gestion des équipements
- **Acteur** : Administrateur.
- **Précondition** : Accès à la base de données.
- **Scénario** : L'administrateur insère les données de localisation (lat/lon) qui sont automatiquement converties en géométries PostGIS via un trigger SQL.

### 3.2.3 Description du cas d’utilisation : Consultation SIG
- **Acteur** : Technicien.
- **Description** : Accès au catalogue GeoNetwork pour rechercher les métadonnées d'une couche spécifique (ex: antennes de la zone Chebba).

---

## 3.3 Conception

### 3.3.1 Diagrammes de séquence
Le diagramme de séquence montre comment les données circulent de l'insertion SQL jusqu'à la mise à jour des index spatiaux.

### 3.3.2 Diagramme de classes
Représentation des entités `Antenne`, `Zone` et `Equipement`.

### 3.3.3 Schéma relationnel et dictionnaire de données
- `antennes` (id, nom, zone, type, latitude, longitude, operateur, geom)

---

## 3.4 Réalisation

### 3.4.1 Architecture logique (diagramme de composants)
Les composants réalisés dans ce sprint sont :
- Le conteneur **PostgreSQL/PostGIS**.
- Le conteneur **GeoNetwork 4.2.7**.

### 3.4.2 Description des interfaces GeoNetwork
L'interface d'administration de GeoNetwork permet de moissonner (harvest) les services OGC et de publier des fiches de métadonnées ISO19139.

---

## Conclusion
Le Sprint 1 s'est achevé avec succès, offrant une infrastructure stable et une base de données fonctionnelle. Le catalogue GeoNetwork est prêt à recevoir les métadonnées géographiques. Le prochain sprint se concentrera sur le développement de l'API Flask pour exposer ces données.

---

# Chapitre 4 : SPRINT 2 – Développement de l’API et exploitation des données GeoNetwork

## Introduction

Le deuxième sprint est dédié à la création de la couche logique du projet. Nous développons une API REST en Python avec le framework Flask pour servir d'intermédiaire entre la base de données et l'interface utilisateur.

---

## 4.1 Backlog du Sprint 2

Les tâches principales de ce sprint sont :
- **Mise en place de l’environnement Python / Flask** : Création du `Dockerfile` et de `app.py`.
- **Connexion à PostgreSQL** : Utilisation de la bibliothèque `psycopg2`.
- **Développement des services API** : Création des routes `/antennes`, `/stats` et `/alerts`.
- **Exploitation des données GeoNetwork** : Mise en place de liens vers les métadonnées.
- **Tests des API** : Validation des réponses JSON avec Postman.

---

## 4.2 Analyse

### 4.2.1 Diagramme de cas d’utilisation
L'utilisateur final interagit avec l'API à travers le dashboard.

### 4.2.2 Description du cas d’utilisation : Consultation des équipements
- **Acteur** : Technicien.
- **Flux** : Le client envoie une requête GET à `/antennes`. L'API interroge la base et renvoie la liste des antennes avec leurs statuts réels.

### 4.2.3 Description du cas d’utilisation : Accès aux données géographiques
- **Flux** : L'API fournit les URLs GeoServer pour l'affichage cartographique.

---

## 4.3 Conception

### 4.3.1 Diagrammes de séquence
Interaction entre React (Frontend), Flask (API) et PostgreSQL.

### 4.3.2 Diagramme de classes
Focus sur les objets de transfert de données (DTO).

### 4.3.3 Schéma relationnel
L'API accède aux tables `antennes` et `mesures`.

---

## 4.4 Réalisation

### 4.4.1 Architecture logique
L'API est structurée en plusieurs modules :
- `routes` : Définition des points d'entrée.
- `database` : Gestion des connexions.
- `logic` : Traitement des données et calculs de statistiques.

### 4.4.2 Description des interfaces API
- `GET /antennes` : Retourne un GeoJSON des antennes.
- `GET /stats` : Retourne les agrégats (Nombre total, état critique, alertes).
- `GET /alerts` : Retourne la liste des anomalies récentes détectées.

---

## Conclusion

Le Sprint 2 a permis de transformer les données brutes de la base en services web accessibles. La plateforme dispose désormais d'un "cerveau" capable de traiter les informations du réseau de Mahdia. Le prochain sprint se concentrera sur l'interface utilisateur et la visualisation.

---

# Chapitre 5 : SPRINT 3 – Supervision des équipements et visualisation des données

## Introduction

Le troisième sprint marque l'aboutissement visuel du projet. Il s'agit de construire l'interface utilisateur interactive (Dashboard) et d'intégrer Grafana pour le monitoring avancé des métriques de performance du réseau.

---

## 5.1 Backlog du Sprint 3

Les tâches de ce sprint incluent :
- **Intégration de Grafana** : Déploiement du conteneur et connexion à PostgreSQL.
- **Création des dashboards** : Conception de graphiques pour le CPU, la RAM et la température.
- **Visualisation cartographique du réseau de Mahdia** : Développement de la carte interactive avec React et Leaflet.
- **Configuration des alertes simples** : Mise en place de seuils critiques (ex: Température > 75°C).

---

## 5.2 Analyse

### 5.2.1 Diagramme de cas d’utilisation
L'utilisateur consulte l'état de santé global du réseau depuis une interface unique.

### 5.2.2 Description du cas d’utilisation : Supervision des équipements
- **Acteur** : Technicien.
- **Scénario** : L'utilisateur ouvre l'onglet "Equipments" et voit en temps réel les dernières mesures reçues.

### 5.2.3 Description du cas d’utilisation : Visualisation cartographique
- **Scénario** : Sur la carte, les antennes changent de couleur (Vert, Jaune, Rouge) selon leur état de santé.

---

## 5.3 Conception

### 5.3.1 Diagrammes de séquence
Demande d'affichage d'un dashboard Grafana imbriqué dans React via une IFrame ou une URL directe.

### 5.3.2 Diagramme de classes
Représentation des composants React (Sidebar, Topbar, Map, StatsCard).

### 5.3.3 Schéma relationnel
Consultation intensive de la table `mesures` pour l'affichage des graphiques temporels.

---

## 5.4 Réalisation

### 5.4.1 Architecture logique
Le frontend est basé sur React avec un style "Glassmorphism" moderne. Les requêtes sont envoyées toutes les 60 secondes pour assurer le temps réel.

### 5.4.2 Description des interfaces Grafana
Les dashboards Grafana permettent de filtrer par zone ou par type d'antenne, offrant une granularité d'analyse importante pour les décideurs.

### 5.4.3 Intégration hybride GeoNetwork
Une fonctionnalité innovante permet de basculer instantanément entre la vue interactive React et le visualiseur cartographique natif de **GeoNetwork** via une IFrame sécurisée. Cela permet aux opérateurs d'utiliser les outils avancés de catalogage SIG sans quitter le dashboard.

---

## Conclusion

À la fin de ce sprint, la plateforme GEO-TÉLÉCOM est pleinement fonctionnelle pour la supervision humaine. Les techniciens de Mahdia peuvent localiser les pannes sur une carte et suivre les performances. Le dernier sprint ajoutera la couche d'intelligence artificielle pour automatiser la détection d'anomalies.

---

# Chapitre 6 : SPRINT 4 – Analyse prédictive et système d’alertes intelligentes

## Introduction

Le dernier sprint du projet apporte la valeur ajoutée de l'intelligence artificielle. Nous implémentons un modèle de détection d'anomalies pour anticiper les comportements anormaux des équipements, allant au-delà des simples seuils statiques.

---

## 6.1 Backlog du Sprint 4

Les tâches réalisées sont :
- **Analyse des données historiques** : Préparation du jeu de données pour l'entraînement.
- **Implémentation du modèle Isolation Forest** : Choix de cet algorithme non supervisé pour sa capacité à détecter des points aberrants dans les métriques réseau.
- **Développement de l’API prédictive** : Route `/predict` pour l'analyse en temps réel.
- **Détection des anomalies** : Marquage automatique des mesures suspectes.
- **Mise en place des alertes intelligentes** : Notification visuelle immédiate sur le dashboard.

---

## 6.2 Analyse

### 6.2.1 Diagramme de cas d’utilisation
L'intelligence artificielle agit comme un acteur système qui surveille le flux de données.

### 6.2.2 Description du cas d’utilisation : Détection d’anomalies
- **Flux** : L'API reçoit les nouvelles mesures, les passe à travers le modèle `IsolationForest` (chargé via Joblib). Si le score est négatif, l'équipement est marqué comme "critique".

### 6.2.3 Description du cas d’utilisation : Alerte intelligente
- **Scénario** : L'IA détecte une corrélation suspecte entre une charge CPU moyenne et une température grimpante, déclenchant une alerte préventive.

---

## 6.3 Conception

### 6.3.1 Diagrammes de séquence
Le processus de prédiction : Collecte de données -> Prétraitement -> Modèle ML -> Notification.

### 6.3.2 Diagramme de classes
Entités liées au Machine Learning : `ModelTrainer`, `Predictor`.

### 6.3.3 Schéma relationnel
Ajout de champs de statut prédictif si nécessaire ou stockage des anomalies dans une table dédiée.

---

## 6.4 Réalisation

### 6.4.1 Architecture logique
Le module IA est intégré directement dans le backend Flask. Il utilise `scikit-learn` et `pandas` pour le traitement des données.

### 6.4.2 Description des interfaces d’alertes
Sur le dashboard, une section "Anomalies détectées par l'IA" affiche les équipements nécessitant une attention immédiate avec une explication textuelle générée.

---

## Conclusion

Le Sprint 4 transforme la plateforme de supervision en un outil d'aide à la décision proactif. Grâce à l'algorithme Isolation Forest, Tunisie Telecom Mahdia peut désormais identifier des pannes subtiles que des seuils classiques ne verraient pas.

---
# Chapitre 7 : Tests, validation et difficultés rencontrées

## Introduction

Cette phase finale est cruciale pour garantir la fiabilité de la plateforme avant sa livraison. Nous présentons les différents tests effectués et les obstacles techniques surmontés durant le projet.

---

## 1. Tests de l’API
Nous avons utilisé Postman pour valider les routes REST.
- **Résultat** : Toutes les routes renvoient des codes 200 OK avec des données JSON valides et structurées.

## 2. Tests du modèle IA
Le modèle `IsolationForest` a été testé sur des données simulées comportant des pics de température anormaux.
- **Résultat** : Le modèle identifie 95% des anomalies injectées manuellement sans générer trop de faux positifs.

## 3. Tests de supervision (Grafana)
Vérification de la mise à jour automatique des graphiques.
- **Résultat** : Les dashboards se rafraîchissent correctement dès l'insertion de nouvelles mesures en base.

## 4. Tests de déploiement (Docker)
Lancement de l'architecture complète sur une machine vierge.
- **Résultat** : La commande `docker-compose up` déploie l'intégralité des 6 services en moins de 5 minutes.

---

## 5. Difficultés rencontrées et solutions

### 5.1 Problèmes de connexion à PostgreSQL
**Problème** : L'API Flask ne parvenait pas à joindre la base de données au démarrage (race condition).
**Solution** : Implémentation d'une boucle de "Wait-for-it" dans le script de démarrage pour attendre que le port 5432 soit prêt.

### 5.2 Absence de données réelles
**Problème** : Difficulté d'accès aux flux de données réels en temps réel durant le stage.
**Solution** : Développement d'un script de simulation sophistiqué (`generate_mesures.py`) basé sur des scénarios réalistes de pannes télécom.

### 5.3 Intégration du modèle IA dans l’API
**Problème** : Consommation mémoire élevée lors du chargement du modèle à chaque requête.
**Solution** : Chargement du modèle une seule fois au démarrage de l'application Flask (Singleton).

### 5.4 Configuration de GeoNetwork avec Docker
**Problème** : Persistance des données du catalogue de métadonnées.
**Solution** : Utilisation de volumes Docker externes pour l'index Lucene et la base H2 interne de GeoNetwork.

---

## Conclusion

Ce chapitre de validation a démontré que la solution GEO-TÉLÉCOM répond aux besoins initiaux de Tunisie Telecom. Malgré les défis techniques liés à l'intégration de services hétérogènes, l'approche par conteneurs a permis de stabiliser la plateforme.

---

# Conclusion générale

Le projet de fin d'études au sein de Tunisie Telecom Mahdia a été une expérience enrichissante, nous permettant de mettre en pratique nos connaissances en développement Full-Stack, en SIG et en Intelligence Artificielle.

La plateforme développée offre une solution concrète à la problématique de la supervision réseau. Elle permet non seulement de visualiser l'état du parc d'antennes sur une carte interactive, mais aussi d'anticiper les incidents grâce à l'analyse prédictive.

**Apports du projet :**
- **Pour l'entreprise** : Une vision unifiée du réseau, une réduction du temps de diagnostic et une transition vers une maintenance préventive.
- **Pour l'étudiant** : Maîtrise de l'écosystème Docker, approfondissement des technologies SIG (Leaflet, PostGIS, GeoServer) et mise en œuvre réelle d'algorithmes de Machine Learning.

**Perspectives :**
- Intégration de flux de données réels via des protocoles SNMP.
- Développement d'une application mobile pour les techniciens sur le terrain.
- Utilisation de modèles de Deep Learning (LSTM) pour des prédictions temporelles encore plus précises.

Ce travail constitue une première étape vers la modernisation numérique des outils de supervision régionale de l'opérateur historique.

---
