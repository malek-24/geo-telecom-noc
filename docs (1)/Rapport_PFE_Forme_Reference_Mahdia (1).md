# Rapport de Projet de Fin d’Études  
## Plateforme de supervision SIG des antennes réseau — Direction régionale Mahdia (Tunisie Telecom)

**Établissement :** [Institut Supérieur … — à compléter]  
**Organisme d’accueil :** Tunisie Telecom — Direction régionale de Mahdia  
**Filière :** [Licence / Ingénieur — à compléter]  
**Année universitaire :** 2025–2026  

**Réalisé par :** Malek [Nom complet]  
**Binôme / partenaire éventuel :** [À compléter ou supprimer]  

**Encadrant académique :** [Prénom Nom]  
**Encadrant professionnel :** [Prénom Nom, Tunisie Telecom Mahdia]  

---

## Dédicace

[Personnaliser comme dans le modèle de rapport : remerciements familiaux, amis, encadrants. Exemple d’amorce :]

À mes parents, pour leur soutien.  
À mes encadrants, pour leur disponibilité et leurs conseils.  
Ce travail vous est dédié.

---

## Remerciements

Nous exprimons notre gratitude à toutes les personnes ayant contribué à la réalisation de ce projet de fin d’études.

Nous remercions particulièrement **[Madame / Monsieur X]**, encadrant(e) académique, pour l’accompagnement, la rigueur scientifique et la pertinence des orientations fournies tout au long du projet.

Nos remerciements vont également à **[Madame / Monsieur Y]** et à l’équipe de la **Direction régionale de Mahdia de Tunisie Telecom**, pour l’accueil en stage, la présentation du contexte métier et la validation des objectifs de la plateforme de supervision.

Nous adressons nos remerciements aux membres du jury pour le temps consacré à l’évaluation de ce travail.

---

## Table des matières

**Introduction générale**

**Chapitre 1 — Présentation du contexte du stage**  
1. Présentation de l’organisme d’accueil  
   1.1 Présentation générale  
   1.2 Organigramme (schéma)  
   1.3 Activités et missions pertinentes pour le projet  
2. Présentation du projet  
   2.1 Contexte général  
   2.2 Problématique  
   2.3 Étude de l’existant  
   2.4 Critique de l’existant  
   2.5 Solution proposée  
   2.6 Méthodologie de travail (Scrum)

**Chapitre 2 — Lancement du projet**  
1. Analyse et spécification des besoins  
   1.1 Identification des acteurs  
   1.2 Besoins fonctionnels et non fonctionnels  
2. Pilotage du projet avec Scrum  
   2.1 Les rôles Scrum  
   2.2 Le backlog produit  
   2.3 Cas d’utilisation global (description textuelle)  
   2.4 Modèle de données / diagramme de classes (vue métier)  
   2.5 Planification des sprints  
3. Architecture de la solution  
   3.1 Architecture logique  
   3.2 Architecture physique (déploiement Docker)

**Chapitre 3 — Sprint 1 : Infrastructure, PostGIS et services SIG**  
1. Planification du sprint  
2. Analyse (cas d’utilisation du sprint)  
3. Conception (séquences, schéma relationnel)  
4. Outils et environnement  
5. Réalisation (captures d’écran à insérer)

**Chapitre 4 — Sprint 2 : API REST, authentification et alimentation des données**  
1. Planification du sprint  
2. Analyse  
3. Conception (API, flux de données)  
4. Outils et environnement  
5. Réalisation (simulation, endpoints)

**Chapitre 5 — Sprint 3 : Tableau de bord React, rôles, analytique et Grafana**  
1. Planification du sprint  
2. Analyse  
3. Conception (séquences, navigation)  
4. Outils et environnement  
5. Réalisation

**Chapitre 6 — Tests, validation et difficultés**

**Conclusion générale**

**Netographie**

**Annexes** (extraits de code, docker-compose, dictionnaire de données)

---

## Liste des abréviations

| Abréviation | Signification |
|-------------|----------------|
| API | Application Programming Interface |
| BTS / eNodeB | Stations de base (terminologie réseau mobile) |
| CU | Cas d’utilisation |
| Docker | Plateforme de conteneurisation |
| GIS / SIG | Système d’information géographique |
| JSON | JavaScript Object Notation |
| ML | Machine Learning (apprentissage automatique) |
| OGC | Open Geospatial Consortium |
| ORM | Object-Relational Mapping (non utilisé ici : SQL direct) |
| PO | Product Owner (Scrum) |
| PostGIS | Extension spatiale de PostgreSQL |
| REST | Representational State Transfer |
| SRID | Spatial Reference System Identifier (ex. 4326) |
| TT | Tunisie Telecom |
| WMS / WFS | Web Map Service / Web Feature Service |

---

# Introduction générale

Les réseaux de télécommunications reposent sur un parc d’équipements distribués géographiquement (antennes, stations, liaisons). Leur bon fonctionnement conditionne la qualité de service perçue par les abonnés. Dans une direction régionale, la supervision consiste à suivre l’état des sites, détecter les dérives (température, charge, signal, trafic) et prioriser les interventions.

Ce projet de fin d’études propose une **plateforme intégrée de supervision** centrée sur le **gouvernorat de Mahdia**, avec :

- un **référentiel géospatial** (PostgreSQL / PostGIS) ;
- la **publication cartographique** (GeoServer) ;
- un **catalogue de métadonnées** (GeoNetwork, avec Elasticsearch et base PostgreSQL dédiée) ;
- une **API REST** (Flask, Python) ;
- un **tableau de bord web** (React) avec carte interactive ;
- une **analyse d’anomalies** (Isolation Forest, scikit-learn) exposée via l’endpoint `/predict` ;
- un outil d’**observabilité** (Grafana) connecté à la base métier pour des tableaux de bord de supervision.

L’objectif pédagogique est de dérouler un cycle complet d’ingénierie logicielle : expression du besoin, modélisation, architecture, implémentation conteneurisée et validation. La méthode **Scrum** organise le travail en sprints courts avec livrables testables.

Le mémoire est structuré comme suit : le **chapitre 1** situe le contexte entreprise et la problématique ; le **chapitre 2** présente les besoins, le backlog et l’architecture ; les **chapitres 3 à 5** décrivent trois sprints successifs ; le **chapitre 6** traite des tests et difficultés ; la **conclusion** ouvre sur les perspectives.

---

# Chapitre 1 — Présentation du contexte du stage

## 1. Présentation de l’organisme d’accueil

### 1.1 Présentation générale

**Tunisie Telecom** est l’opérateur historique des télécommunications en Tunisie. L’entreprise assure des services fixes et mobiles, l’accès Internet et des offres aux entreprises. La **direction régionale de Mahdia** pilote le déploiement et la maintenance des équipements sur le territoire régional.

**Fiche signalétique (à adapter si ton institut impose un modèle précis) :**

| Élément | Détail |
|--------|--------|
| Raison sociale | Tunisie Telecom |
| Secteur | Télécommunications |
| Direction d’accueil | Direction régionale Mahdia |
| Mission liée au PFE | Supervision et visualisation de l’état du réseau d’antennes (données simulées / démonstrateur) |

### 1.2 Organigramme

[Insérer ici une figure : organigramme simplifié de la direction régionale ou du service technique, ou une légende « non communiqué — schéma indicatif » si confidentiel.]

### 1.3 Activités pertinentes pour le projet

- Suivi des sites et des équipements actifs.  
- Exploitation d’indicateurs de charge et d’environnement (température, CPU dans le démonstrateur).  
- Besoin de **vue cartographique** et de **consolidation** des indicateurs pour l’aide à la décision.

---

## 2. Présentation du projet

### 2.1 Contexte général

Le projet consiste à concevoir un **démonstrateur** de plateforme de supervision : les mesures sont **injectées par simulation** (scripts Python, dossier `simulation/`) dans une base PostGIS, puis consommées par une API et un dashboard. Cette approche permet de valider l’architecture sans dépendre immédiatement des flux opérationnels de production.

### 2.2 Problématique

**Comment offrir une vision unifiée, cartographique et analytique de l’état des antennes, tout en restant modulaire et déployable par conteneurs ?**

Sous-questions : centralisation des mesures, exposition standardisée (REST), séparation des rôles côté interface, complémentarité entre supervision « métier » (React) et tableaux de bord « infra » (Grafana).

### 2.3 Étude de l’existant (typique direction régionale)

- Données parfois **dispersées** (fichiers, outils hétérogènes).  
- Supervision souvent **réactive** (intervention après constat).  
- Peu de **chaîne SIG + API + web** unifiée dans un environnement de démonstration pédagogique.

### 2.4 Critique de l’existant

- Manque d’une **carte interactive** commune pour localiser rapidement les sites sensibles.  
- Absence d’un **bus de données unifié** dans le périmètre du PFE (remplacé ici par PostgreSQL + API).  
- Les outils avancés d’IA en production nécessitent garde-fous ; le PFE se limite à un **module explicatif** (`/predict`).

### 2.5 Solution proposée

Une plateforme **GEO-supervision** composée de :

1. **Données** : tables `antennes`, `mesures`, vues `antennes_statut` et `antennes_geo` (dernière mesure par site).  
2. **SIG** : GeoServer sur les données PostGIS ; GeoNetwork pour le catalogue.  
3. **Application** : Flask + React + nginx (proxy `/api`).  
4. **Observabilité** : Grafana avec provisioning de datasource et dashboard JSON dans le dépôt.

### 2.6 Méthodologie de travail — Scrum

**Rôles :**

| Rôle Scrum | Attribution suggérée |
|------------|----------------------|
| Product Owner | Encadrant professionnel (validation du besoin) |
| Scrum Master | Étudiant |
| Équipe de développement | Étudiant(s) |

**Cérémonies :** planification de sprint, suivi (daily adapté en hebdomadaire en stage), revue de sprint, rétrospective.

**Durée indicative :** trois sprints (voir chapitre 2) pour coller à une structuration « rapport type » ; on peut aussi regrouper en 4 itérations en annexe sans changer le fond.

---

# Chapitre 2 — Lancement du projet

## 1. Analyse et spécification des besoins

### 1.1 Identification des acteurs

Les acteurs **métier** suivants interagissent avec le système via le dashboard (les rôles techniques `administrateur`, `moderateur`, `utilisateur` sont alignés sur le code : `dashboard/src/auth/roles.js` et comptes démo dans `docker-compose.yml` / `api/app.py`).

| Acteur | Description |
|--------|-------------|
| **Utilisateur** | Consulte dashboard, carte, antennes, anomalies, rapports. |
| **Modérateur** | Même périmètre + page **Modération** (contrôle / cohérence des données — périmètre démo). |
| **Administrateur** | Même périmètre utilisateur + page **Administration** (gestion des comptes et paramètres — maquette / texte de démo). |

**Important pour les diagrammes UML :** ne pas présenter une généralisation « Modérateur hérite d’Administrateur » si cela suggère que le modérateur gère les comptes : **seul l’administrateur** accède à `/administration` dans l’application.

| Route principale | Rôles autorisés (implémentation) |
|------------------|-----------------------------------|
| `/dashboard`, `/map`, `/equipments`, `/analytics`, `/rapports` | les trois rôles |
| `/moderation` | administrateur, modérateur |
| `/administration` | administrateur uniquement |

### 1.2 Besoins fonctionnels (extraits)

| ID | Besoin |
|----|--------|
| BF1 | S’authentifier et conserver une session (token signé côté API, stockage local côté client). |
| BF2 | Visualiser les antennes et leur dernier statut (normal / alerte / critique). |
| BF3 | Afficher des indicateurs agrégés (totaux, répartition par statut, nombre de zones). |
| BF4 | Lister les alertes récentes (équipements en alerte ou critique). |
| BF5 | Proposer une analyse d’anomalies spatiales (Isolation Forest sur lat/lon — démonstrateur). |
| BF6 | Publier les données pour GeoServer (vue `antennes_geo`). |
| BF7 | Disposer d’un catalogue de métadonnées (GeoNetwork). |
| BF8 | Superviser via Grafana (requêtes sur la base `antennes_mahdia`). |

### Besoins non fonctionnels (extraits)

| ID | Besoin |
|----|--------|
| BNF1 | Déploiement reproductible (**Docker Compose**, réseau `sig_net`). |
| BNF2 | Séparation frontend / backend ; CORS activé sur l’API. |
| BNF3 | Temps de réponse API acceptable pour un nombre limité d’antennes (PFE). |
| BNF4 | **Sécurité** : authentification de **démonstration** (mots de passe en clair dans le compose) — à ne pas présenter comme niveau production. |

---

## 2. Pilotage du projet avec Scrum

### 2.1 Rôles Scrum

[Déjà décrit en 2.6 ; dupliquer une phrase sur la validation par le PO à chaque fin de sprint.]

### 2.2 Backlog produit (synthèse)

| # | User story (résumé) | Priorité |
|---|---------------------|----------|
| US1 | En tant qu’utilisateur, je veux voir les antennes sur une carte avec leur statut. | Haute |
| US2 | En tant qu’utilisateur, je veux consulter les KPI globaux du réseau. | Haute |
| US3 | En tant qu’utilisateur, je veux voir les alertes actives. | Haute |
| US4 | En tant qu’administrateur, je veux distinguer les rôles et protéger certaines pages. | Moyenne |
| US5 | En tant qu’analyste, je veux une vue « anomalies » pour expérimenter l’IA. | Moyenne |
| US6 | En tant qu’exploitant, je veux Grafana pour des graphiques sur PostgreSQL. | Moyenne |
| US7 | En tant qu’architecte SIG, je veux GeoServer + GeoNetwork dans la même stack. | Basse à moyenne |

### 2.3 Cas d’utilisation global (description textuelle)

Le système « **Supervision télécom** » permet : authentification ; consultation du tableau de bord ; supervision des équipements ; consultation de la carte ; accès aux rapports ; pour certains rôles, modération et administration. Les données proviennent de la base alimentée par simulation. Les services SIG et Grafana sont accessibles en parallèle du dashboard.

[Insérer la figure du diagramme de cas d’utilisation une fois dessinée.]

### 2.4 Diagramme de classes (vue métier simplifiée)

Entités principales :

- **Antenne** : identifiant, nom, zone, type (fixe/mobile), coordonnées, géométrie PostGIS.  
- **Mesure** : référence antenne, température, CPU, signal, trafic, date ; **statut** calculé en base selon des seuils.  
- **Vue AntenneStatut** : projection « dernière mesure » pour l’API et l’UI.  
- **Vue AntenneGeo** : pour la couche GeoServer.

### 2.5 Planification des sprints

| Sprint | Objectif principal | Livrable |
|--------|-------------------|----------|
| **Sprint 1** | Infra, base PostGIS, init.sql, GeoServer, GeoNetwork, Compose | Stack qui démarre, schéma données + vues |
| **Sprint 2** | API Flask (auth, `/stats`, `/alerts`, `/antennes`, `/predict`), simulation | JSON testés, données qui circulent |
| **Sprint 3** | React (pages, rôles), Grafana, finitions UX | Application complète démo |

---

## 3. Architecture de la solution

### 3.1 Architecture logique

- **Présentation :** navigateur → dashboard React (port hôte **3000** via nginx).  
- **API :** Flask (**5000**), requêtes SQL via `psycopg2` / `pandas`.  
- **Données métier :** PostgreSQL **antennes_mahdia** (PostGIS).  
- **Catalogue :** GeoNetwork + **geonetwork_db** + **Elasticsearch**.  
- **Cartographie :** GeoServer (**8081**) lit PostGIS.  
- **Monitoring :** Grafana (**3001**), provisioning dans `grafana/provisioning/`.

Les scripts de **simulation** injectent des lignes dans `mesures`.

### 3.2 Architecture physique (Docker)

Tous les services partagent le réseau **`sig_net`**. Volumes nommés pour la persistance (`postgres_data`, `geoserver_data`, etc.). Healthchecks sur PostgreSQL, Elasticsearch et services dépendants.

**Ports hôte (rappel) :** 3000 frontend, 5000 API, 5432 PostGIS, 8080 GeoNetwork, 8081 GeoServer, 3001 Grafana, 9200 Elasticsearch.

[Insérer figures : schéma de déploiement — export depuis `docs/architecture_rapport_PFE.md` (Mermaid) si besoin.]

---

# Chapitre 3 — Sprint 1 : Infrastructure, PostGIS et services SIG

## 1. Planification du sprint

**Objectifs :** disposer d’un environnement Docker stable ; créer le schéma relationnel et les vues ; activer PostGIS ; lancer GeoServer et GeoNetwork.

**Sprint backlog (exemple) :**

| Tâche | Critère de done |
|-------|-----------------|
| Rédiger `docker-compose.yml` | `docker compose up -d` sans erreur bloquante |
| Écrire `database/init.sql` | Tables + triggers + vues créés au premier démarrage |
| Configurer GeoServer (manuel) | Couche publiée sur la vue spatiale |
| Vérifier GeoNetwork | UI accessible, dépendances DB/ES vertes |

## 2. Analyse

Cas d’utilisation typiques du sprint : « Initialiser la base », « Publier une couche SIG », « Documenter une ressource dans le catalogue ».

## 3. Conception

- **Schéma relationnel :** `antennes`, `mesures`, vues `antennes_statut`, `antennes_geo`.  
- **Règles de statut :** colonne générée sur `mesures` (seuils température / CPU).  
- **Séquence type :** insertion antenne → trigger `geom` → insertion mesures → mises à jour des vues.

## 4. Outils et environnement

Docker Desktop, éditeur, client SQL (pgAdmin ou `psql`), navigateur pour GeoServer / GeoNetwork.

## 5. Réalisation

[Captures : Docker Compose, écran GeoServer, écran GeoNetwork, modèle de données sous pgAdmin.]

---

# Chapitre 4 — Sprint 2 : API REST, authentification et données

## 1. Planification du sprint

**Objectifs :** exposer les données via Flask ; sécuriser un minimum l’accès par rôles démo ; alimenter la base par simulation.

**Sprint backlog (exemple) :**

| Tâche | Livrable |
|-------|----------|
| Routes `/stats`, `/alerts`, `/antennes` | JSON conforme au dashboard |
| Auth `/auth/login`, `/auth/me` | Token signé (`itsdangerous`) |
| Scripts `simulation/*.py` | Mesures périodiques |
| Tests manuels Postman | Jeu de requêtes documenté |

## 2. Analyse

Description textuelle des CU : « Consulter les statistiques », « Lister les antennes avec coordonnées », « Recevoir les alertes ».

## 3. Conception

- **Séquence :** Client → `GET /antennes` → Flask → requête sur `antennes_statut` JOIN `antennes` → JSON.  
- **Endpoint `/predict` :** chargement des coordonnées → `IsolationForest` → champ `anomaly` (**1** = anomalie, **0** = normal) après mapping des labels scikit-learn.

## 4. Outils et environnement

Python 3, Flask, pandas, scikit-learn, psycopg2, Postman.

## 5. Réalisation

- Fichier principal : `api/app.py`.  
- Comptes démo : variables `AUTH_USER_*` / `AUTH_PASS_*` dans Compose.  
- CORS ouvert pour le développement.

[Captures : Postman sur `/stats`, réponse `/predict`.]

---

# Chapitre 5 — Sprint 3 : Tableau de bord React, rôles, analytique et Grafana

## 1. Planification du sprint

**Objectifs :** pages complètes, navigation par rôle, intégration carte, page analytique, Grafana.

**Sprint backlog (exemple) :**

| Tâche | Livrable |
|-------|----------|
| Pages Dashboard, Map, Equipments, Analytics, Rapports | UI fonctionnelle |
| `ProtectedRoute` + `roles.js` | Contrôle d’accès cohérent |
| Proxy `/api` (nginx + `setupProxy` en dev) | Pas de CORS bloquant en démo |
| Dashboard Grafana JSON | Visualisation PostgreSQL |

## 2. Analyse

CU : « Superviser les équipements », « Consulter les anomalies », « Modérer » (rôles autorisés), « Administrer » (admin seul).

## 3. Conception

- Composants : `Sidebar`, `Topbar`, `KPI`, `Alerts`, cartes Leaflet, etc.  
- Rafraîchissement périodique des données (fichier `dataRefreshMs.js`).

## 4. Outils et environnement

Node.js, React, React Router, Leaflet, nginx (image dashboard).

## 5. Réalisation

[Captures : login, dashboard, carte, page analytics, Grafana, page administration vs moderation selon compte.]

---

# Chapitre 6 — Tests, validation et difficultés

## 1. Tests API

Vérification des codes HTTP et de la structure JSON pour `/stats`, `/alerts`, `/antennes`, `/predict`, `/auth/login`.

## 2. Tests interface

Scénarios par rôle : l’utilisateur standard ne doit pas accéder à `/administration` ; le modérateur accède à `/moderation`.

## 3. Tests de déploiement

Relève du démarrage complet avec `docker compose up` ; vérification des healthchecks.

## 4. Difficultés rencontrées (exemples)

- **Ordre de démarrage :** l’API attend la disponibilité PostgreSQL (retry dans `get_conn`).  
- **Cohérence SIG :** paramétrage manuel GeoServer (workspace, datastore, couche).  
- **Données réelles :** utilisation de la **simulation** pour démontrer la chaîne bout en bout.

---

# Conclusion générale

Le projet réalise une **plateforme de supervision SIG** modulaire pour la direction régionale de Mahdia, en intégrant les standards ouverts (PostGIS, OGC, REST) et des outils d’exploitation (Grafana). L’architecture conteneurisée facilite la reproduction de l’environnement sur une autre machine.

**Limites :** authentification faible (démo), jeu de données simulé, modèle `/predict` pédagogique sur les coordonnées géographiques.

**Perspectives :** branchement à des métriques réelles (SNMP, supervision existante), durcissement sécuritaire (OAuth2 / LDAP), modèles séries temporelles sur l’historique `mesures`, application mobile terrain.

---

# Netographie

[À compléter selon les sources réellement citées dans ta version finale Word. Exemples de types de références :]

1. Documentation PostGIS — https://postgis.net/documentation/  
2. Documentation GeoServer — https://docs.geoserver.org/  
3. Documentation GeoNetwork — https://geonetwork-opensource.org/  
4. Flask — https://flask.palletsprojects.com/  
5. React — https://react.dev/  
6. Scikit-learn — IsolationForest — https://scikit-learn.org/  
7. Manifeste Agile (2001) — https://agilemanifesto.org/  
8. Scrum Guide — https://scrumguides.org/  

---

# Annexes

## Annexe A — Dictionnaire de données (résumé)

| Table / vue | Description |
|-------------|-------------|
| `antennes` | Référentiel des sites et géométrie |
| `mesures` | Historique des mesures et statut dérivé |
| `antennes_statut` | Dernière mesure par antenne (dashboard / API) |
| `antennes_geo` | Dernière mesure + `geom` (GeoServer) |

## Annexe B — Endpoints API

| Méthode | Route | Rôle |
|---------|-------|------|
| GET | `/` | Santé |
| POST | `/auth/login` | Public |
| GET | `/auth/me` | Bearer |
| GET | `/stats` | Données |
| GET | `/alerts` | Données |
| GET | `/antennes` | Données |
| GET | `/predict` | Données |

## Annexe C — Comptes de démonstration

| Utilisateur | Mot de passe | Rôle |
|-------------|--------------|------|
| admin | admin123 | administrateur |
| moderateur | mod123 | moderateur |
| utilisateur | user123 | utilisateur |

*(À retirer ou anonymiser dans un rapport public.)*

---

*Document généré pour servir de base au mémoire PFE, sur le modèle de structure du rapport de référence (dédicace, remerciements, introduction, chapitres, sprints, conclusion, netographie). Adapter les champs [à compléter], insérer les figures et la bibliographie finale dans Word ou LaTeX.*
