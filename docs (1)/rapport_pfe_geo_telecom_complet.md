# INTRODUCTION GÉNÉRALE

**Présentation du projet**
Le secteur des télécommunications est aujourd'hui confronté à une explosion du trafic de données et à une complexification croissante des infrastructures réseaux. Pour garantir une qualité de service (QoS) irréprochable, la supervision des équipements en temps réel est devenue une nécessité absolue. C'est dans ce contexte que s'inscrit le présent Projet de Fin d'Études (PFE), intitulé « Développement d’une plateforme de supervision et d’analyse prédictive de panne des équipements : cas Tunisie Télécom de Mahdia ». Ce projet vise à concevoir et développer la plateforme GEO-TÉLÉCOM NOC, une solution web intelligente intégrant des Systèmes d'Information Géographique (SIG) et de l'Intelligence Artificielle (IA).

**Problématique**
Actuellement, la détection des anomalies sur les antennes et équipements réseau s'appuie souvent sur des méthodes réactives : les équipes techniques n'interviennent qu'une fois la panne survenue ou signalée par les abonnés. La supervision manque d'une centralisation visuelle forte (cartographie dynamique) et d'un outil capable d'anticiper les défaillances matérielles ou logicielles (surchauffe, baisse de débit, saturation CPU) avant qu'elles n'impactent le réseau. Comment alors passer d'une maintenance réactive à une maintenance prédictive tout en offrant une visualisation géospatiale intuitive aux opérateurs ?

**Objectifs**
L'objectif principal est de développer une plateforme centralisée capable de :
* Superviser en temps réel l'état de santé des équipements réseau de la région de Mahdia.
* Afficher géographiquement les antennes et leurs statuts via une cartographie interactive.
* Analyser les métriques de télémétrie à l'aide d'un modèle d'Intelligence Artificielle pour détecter et prédire les pannes.
* Automatiser la génération d'alertes intelligentes et la gestion des tickets d'intervention.

**Méthodologie adoptée**
Pour mener à bien ce projet, nous avons adopté la méthodologie agile Scrum, permettant une approche itérative et incrémentale. Le développement a été découpé en Sprints successifs, favorisant l'adaptabilité face aux besoins techniques et fonctionnels.

**Organisation du rapport**
Le présent rapport est structuré en six chapitres. Le Chapitre 1 expose le cadre général du projet et l'analyse de l'existant. Le Chapitre 2 détaille la préparation, les besoins et l'architecture du système. Le Chapitre 3 présente le Sprint 1 consacré à l'infrastructure SIG. Le Chapitre 4 aborde le Sprint 2 dédié au backend. Le Chapitre 5 décrit le Sprint 3 centré sur le frontend et le tableau de bord. Enfin, le Chapitre 6 présente le Sprint 4 portant sur l'Intelligence Artificielle et la validation globale du système.

---

# CHAPITRE 1 — CADRE GÉNÉRAL DU PROJET

## Introduction
Ce premier chapitre vise à situer le projet dans son contexte professionnel. Nous y présenterons l'organisme d'accueil, Tunisie Télécom, puis nous analyserons l'existant afin de justifier techniquement et fonctionnellement la solution proposée. Enfin, nous décrirons la démarche méthodologique adoptée pour la réalisation de ce projet.

## 1.1 Présentation de l’organisme d’accueil
### 1.1.1 Présentation de Tunisie Télécom
Tunisie Télécom (TT) est l'opérateur historique de télécommunications en Tunisie. L'entreprise offre une gamme complète de services incluant la téléphonie fixe, mobile, et l'accès à Internet pour le grand public et les entreprises. 
### 1.1.2 Direction régionale de Mahdia
Le projet se concentre spécifiquement sur le réseau de la Direction Régionale de Mahdia, chargée du maintien et de l'optimisation des infrastructures de télécommunications sur l'ensemble du gouvernorat.
### 1.1.3 Activités et services
La direction assure le déploiement de la fibre optique, l'entretien des stations de base (BTS/NodeB/eNodeB) et la garantie de la continuité des services voix et data.
### 1.1.4 Organisation du service technique
Le service technique est composé d'ingénieurs réseaux et de techniciens de terrain (Drive Test, maintenance) qui collaborent pour diagnostiquer et réparer les dysfonctionnements du réseau.

## 1.2 Cadre du projet
### 1.2.1 Contexte du projet
*   **Importance de la supervision réseau** : Un réseau non supervisé est un réseau aveugle. La surveillance continue des indicateurs clés (KPIs) est indispensable pour garantir la satisfaction client.
*   **Gestion intelligente des équipements** : Le nombre d'équipements augmentant, il devient impossible de les vérifier manuellement. Une gestion centralisée s'impose.
*   **Détection prédictive des pannes** : L'exploitation des données historiques (Big Data) permet aujourd'hui d'anticiper les pannes avant la rupture de service.

### 1.2.2 Analyse de l’existant
#### 1.2.2.1 Étude de l’existant
*   **Méthodes actuelles de supervision** : Utilisation de tableaux de bord classiques affichant des listes d'alarmes textuelles.
*   **Outils utilisés** : Outils constructeurs propriétaires (Huawei, Ericsson) souvent cloisonnés.
*   **Processus de maintenance** : Ouverture de tickets manuel, déplacement des techniciens suite à la remontée d'une alarme critique.

#### 1.2.2.2 Critiques de l’existant
*   **Manque de centralisation** : L'éparpillement des outils complique le diagnostic.
*   **Surveillance limitée** : L'absence de corrélation avancée entre les métriques empêche une vision globale.
*   **Détection tardive des anomalies** : Les alertes se déclenchent au dépassement de seuils statiques (post-panne).
*   **Intervention corrective lente** : Le temps de localisation exacte de la panne et d'attribution aux techniciens est perfectible.

#### 1.2.2.3 Solution proposée
Pour pallier ces limites, nous proposons GEO-TÉLÉCOM NOC :
*   **Plateforme web centralisée** : Accessible via navigateur, unifiant toutes les données.
*   **Tableau de bord interactif** : Affichage temps réel des KPIs.
*   **Analyse intelligente des équipements** : Moteur IA pour la détection précoce d'anomalies multidimensionnelles.
*   **Cartographie des équipements** : SIG intégré pour localiser les antennes et visualiser les zones critiques.

## 1.3 Méthodologie de travail
### 1.3.1 Méthodes agiles
Les méthodes agiles privilégient la communication, l'adaptation au changement et la livraison continue de logiciels fonctionnels, s'opposant ainsi aux méthodes traditionnelles en cascade (Waterfall).
### 1.3.2 Méthodologie Scrum
*   **Product Backlog** : Liste priorisée des fonctionnalités attendues.
*   **Sprint Planning** : Réunion définissant les objectifs d'une itération de 2 à 3 semaines.
*   **Sprint Review** : Démonstration du travail accompli à la fin du sprint.
### 1.3.3 Langages de modélisation
*   **UML (Unified Modeling Language)** : Langage standardisé essentiel pour cartographier visuellement l'architecture logicielle.
*   **Diagrammes utilisés** : Cas d'utilisation, classes, séquences, et composants.

## Conclusion
L'étude de l'existant a mis en exergue la nécessité d'innover dans la supervision réseau. La proposition d'une plateforme intelligente couplée à la méthodologie Scrum établit un cadre solide pour entamer la phase de conception logicielle.

---

# CHAPITRE 2 — PRÉPARATION DU PROJET

## Introduction
Ce chapitre est consacré à la spécification détaillée des besoins et à la modélisation fonctionnelle du système. Il détaille également l'environnement technologique sélectionné et l'architecture logicielle globale qui supportera l'ensemble des futurs développements.

## 2.1 Capture des besoins
### 2.1.1 Besoins fonctionnels
*   **Authentification** : Connexion sécurisée avec des identifiants stricts.
*   **Consultation des équipements** : Visualisation en temps réel de l'état de chaque antenne.
*   **Tableau de bord de supervision** : Agrégation des données (sites critiques, alertes).
*   **Gestion des alertes** : Traitement et résolution des tickets d'incidents.
*   **Analyse prédictive** : Détection des anomalies via IA et génération de diagnostics.
*   **Cartographie géographique** : Intégration d'une carte interactive (Leaflet/WMS).
*   **Gestion utilisateurs** : Création, modification et suppression des comptes (CRUD).

### 2.1.2 Besoins non fonctionnels
*   **Sécurité** : Protection des API via JWT, hachage des mots de passe.
*   **Performance** : Temps de réponse optimisés, traitement de données en arrière-plan.
*   **Disponibilité** : Tolérance aux pannes via la conteneurisation Docker.
*   **Facilité d’utilisation** : Interface UX/UI fluide et réactive (Single Page Application).

### 2.1.3 Modélisation des besoins
**Identification des acteurs** : Administrateur, Ingénieur Réseau, Technicien Terrain.
**Diagramme de cas d’utilisation global** : Ce diagramme (non figuré) illustre l'accès exclusif de l'administrateur à la gestion des utilisateurs, tandis que les ingénieurs supervisent la carte, consultent les prédictions IA et gèrent les tickets avec les techniciens.

## 2.2 Gestion du projet avec Scrum
### 2.2.1 Équipe et rôles
Product Owner (garant du besoin métier), Scrum Master (facilitateur), et Développeur (réalisation technique).
### 2.2.2 Product backlog
Recensement exhaustif sous forme de *User Stories* (ex: "En tant qu'Ingénieur, je veux visualiser les antennes sur une carte").
### 2.2.3 Planification des sprints
Structuration du projet en 4 Sprints (Infrastructure, Backend, Frontend, IA).

## 2.3 Environnement de travail
### 2.3.1 Environnement matériel
Développement réalisé sur un ordinateur performant (Processeur i7/Ryzen, 16Go RAM) nécessaire à l'orchestration locale des conteneurs et des serveurs cartographiques.
### 2.3.2 Environnement logiciel
**Outils**
*   **Docker** : Conteneurisation des services.
*   **VS Code** : Éditeur de code (IDE).
*   **GitHub** : Gestion de versions.
**Langages**
*   **Python** (Backend, IA), **JavaScript** (Frontend), **SQL** (Base de données).
**Frameworks et technologies**
*   **Flask** : Framework API Python léger.
*   **ReactJS** : Bibliothèque JavaScript pour les interfaces utilisateur.
*   **PostgreSQL/PostGIS** : SGBD relationnel avec extension spatiale.
*   **GeoServer** : Serveur cartographique Open Source (WMS).
*   **GeoNetwork** : Catalogue de métadonnées spatiales.
*   **Docker** : Orchestration et isolation.

## 2.4 Architecture
### 2.4.1 Architecture globale
Le système adopte une architecture microservices orientée services web, permettant une évolutivité et une indépendance de chaque brique applicative.
### 2.4.2 Architecture applicative
*   **Frontend ReactJS** : Couche de présentation cliente (Port 3000).
*   **Backend Flask** : Couche métier et contrôleur logique (Port 5000).
*   **Base PostgreSQL/PostGIS** : Couche d'accès et persistance des données.
*   **GeoNetwork + Elasticsearch** : Couche d'indexation géospatiale.
*   **GeoServer** : Couche de rendu cartographique.
*   **Module IA** : Algorithmes prédictifs intégrés au backend.

## Conclusion
La définition exhaustive des besoins et le choix assumé d'une stack technologique de pointe (React, Flask, Docker, SIG) préparent le terrain pour le lancement du développement technique lors du premier Sprint.

---

# CHAPITRE III : SPRINT 1 – Mise en place de l’infrastructure et intégration des outils géospatiaux

## Introduction
*   **Objectifs du Sprint 1** : Créer l'ossature du projet en déployant une infrastructure stable, isolée et orientée SIG.
*   **Mise en place de l’environnement technique** : Utilisation exclusive de Docker pour orchestrer les bases de données et les serveurs géographiques.
*   **Rôle du sprint dans la construction de la plateforme** : Il constitue le socle de données ; sans cette base, ni l'API ni le frontend ne peuvent exister.

## 3.1 Backlog du Sprint 1
*   Installation et configuration de Docker.
*   Déploiement de GeoNetwork.
*   Installation et configuration de GeoServer.
*   Configuration de PostgreSQL/PostGIS.
*   Intégration des données géographiques des antennes (coordonnées GPS).
*   Configuration de la communication entre GeoServer et PostgreSQL/PostGIS (Création d'un entrepôt de données).
*   Configuration d’Elasticsearch avec GeoNetwork.

## 3.2 Analyse
### 3.2.1 Diagramme de cas d’utilisation
Gérer les antennes (CRUD base de données), Visualiser les données géographiques (Système backend), Consulter les couches cartographiques (Requêtes WMS).
### 3.2.2 Description du cas d’utilisation : Gestion des antennes
*   **Acteur** : Système / Administrateur de base de données.
*   **Description** : Insertion, mise à jour ou suppression des points géographiques.
*   **Préconditions / Postconditions** : Base PostGIS active / Données géométriques validées.
### 3.2.3 Description du cas d’utilisation : Consultation des données géographiques
*   **Acteur** : Utilisateur (via client SIG).
*   **Description** : Demande d'affichage d'une carte thématique.
*   **Résultat attendu** : Rendu d'une image matricielle superposable (Couche WMS).

## 3.3 Conception
### 3.3.1 Diagrammes de séquence
Interactions utilisateur – GeoServer – GeoNetwork – Base de données : L'utilisateur effectue une requête, GeoServer interroge PostGIS, compile les styles (SLD) et renvoie la tuile cartographique.
### 3.3.2 Diagramme de classes
*   **Antenne** : Entité métier.
*   **Site** : Regroupement géographique.
*   **Localisation** : Attribut de type `Point (Longitude, Latitude)`.
### 3.3.3 Schéma relationnel et dictionnaire de données
*   **Tables** : `antennes` (id, nom, type, zone, geom).
*   **Relations** : Clés primaires et typage.
*   **Structure des données géographiques** : Utilisation du standard EPSG:4326 (WGS84).

## 3.4 Réalisation
### 3.4.1 Architecture logique (diagramme de composants)
Le réseau Docker `sig_net` lie le conteneur `postgres`, `geoserver`, et `geonetwork`.
### 3.4.2 Installation et configuration des outils
*   **Déploiement Docker** : Écriture d'un fichier `docker-compose.yml`.
*   **Configuration PostgreSQL/PostGIS** : Initialisation avec des scripts SQL automatisés (`init_db.sql`).
*   **Configuration GeoServer** : Création d'un *Workspace* "telecom_mahdia" et d'un *Store* lié à PostGIS via l'API REST de GeoServer.
*   **Configuration GeoNetwork** : Connexion à l'annuaire d'entreprise.
*   **Intégration Elasticsearch avec GeoNetwork** : Indexation rapide des métadonnées pour des recherches fulgurantes.
### 3.4.3 Description des interfaces
*   **Interface GeoNetwork** : Portail de recherche d'objets spatiaux.
*   **Interface GeoServer** : Panneau d'administration web pour styliser (Layer preview).
*   **Visualisation des couches géographiques** : Prévisualisation OpenLayers confirmant l'affichage des points sur Mahdia.

## 3.5 Tests et validation
*   **Test des conteneurs Docker** : Commande `docker ps` confirmant l'état *Up* et *Healthy*.
*   **Validation de la connexion PostgreSQL/PostGIS** : Tests de requêtes `ST_AsText(geom)` réussis.
*   **Validation GeoServer & GeoNetwork** : Accès aux interfaces d'administration sur les ports 8080 et 8081.

## Conclusion
Le Sprint 1 s'achève sur une réussite totale. La mise en place de l'infrastructure géospatiale constitue un backend de données robuste et prêt à être consommé par nos futures API.

---

# CHAPITRE IV : SPRINT 2 – Développement du backend et des API REST

## Introduction
*   **Objectifs du Sprint 2** : Créer le cœur logique (API) servant d'interface entre la base de données complexe et le futur tableau de bord.
*   **Continuité avec le Sprint 1** : L'API exploitera les tables générées lors du Sprint précédent.

## 4.1 Backlog du Sprint 2
*   Mise en place de l’environnement Python/Flask.
*   Connexion à PostgreSQL/PostGIS (via `psycopg2`).
*   Développement des API REST (Authentification, CRUD).
*   Gestion des données des antennes et télémétrie.
*   Exploitation des données géographiques via requêtes SQL spécifiques.
*   Tests des API avec Postman.

## 4.2 Analyse
### 4.2.1 Diagramme de cas d’utilisation
Consulter les antennes via l’API, Accéder aux données géographiques JSON, Gérer les informations des antennes.
### 4.2.2 Description du cas d’utilisation : Consultation des antennes
*   **Description** : Requête HTTP GET vers `/api/antennes`.
*   **Résultat attendu** : Une réponse JSON formatée listant tous les équipements.
### 4.2.3 Description du cas d’utilisation : Accès aux données géographiques
*   **Description** : Requête ciblant les métadonnées de localisation (latitude, longitude).
*   **Données retournées** : Structure compatible avec un affichage cartographique (Type FeatureCollection ou JSON annoté).

## 4.3 Conception
### 4.3.1 Diagrammes de séquence
Le client envoie un token JWT, l'API Flask (Décorateur `@token_required`) valide le token, interroge PostgreSQL, formate le résultat et renvoie un JSON (HTTP 200).
### 4.3.2 Diagramme de classes
*   **Antenne** : Hérite des attributs de Site et Localisation dans la structure objet Python (Dictionnaires).
### 4.3.3 Schéma relationnel
*   **Relations entre les tables** : `users` (auth), `antennes_statut` (historique) liées par clé étrangère `antenne_id`.

## 4.4 Réalisation
### 4.4.1 Architecture logique
*   **API Flask** (`app.py`, Blueprints `/routes`).
*   **PostgreSQL/PostGIS** (Stockage).
*   **GeoServer / GeoNetwork** (Non concernés directement par l'API JSON métier, mais parallèles).
### 4.4.2 Développement des API REST
*   **Endpoint /antennes** : Renvoie la liste complète des antennes fusionnée avec leur dernier statut connu.
*   **Endpoint /sites & /localisations** : Routes dédiées à la topologie réseau.
### 4.4.3 Intégration backend/base de données
*   **Connexion PostgreSQL/PostGIS** : Utilisation d'un fichier utilitaire `connection.py` gérant un pool de connexions robuste.
*   **Gestion des requêtes SQL** : Paramétrage pour éviter les injections SQL (`%s`).
*   **Traitement des données géographiques** : Extraction des coordonnées `ST_Y(geom::geometry)` et `ST_X(geom::geometry)`.

## 4.5 Tests et validation
*   **Tests API avec Postman** : Simulation des requêtes GET, POST, PUT, DELETE.
*   **Validation des endpoints** : Vérification des codes de retour (200 OK, 401 Unauthorized, 403 Forbidden).
*   **Vérification des données retournées** : Conformité du payload JSON avec le contrat d'interface attendu par le frontend.

## Conclusion
La validation du Sprint 2 garantit un Backend et des API REST totalement fonctionnels, sécurisés et performants, ouvrant la voie à la conception de l'interface visuelle.

---

# CHAPITRE V : SPRINT 3 – Développement de l’interface web et tableau de bord de supervision

## Introduction
*   **Objectifs du Sprint 3** : Donner vie aux données en développant une interface utilisateur riche, interactive et ergonomique.
*   **Mise en place de la supervision visuelle des antennes** : Le NOC (Network Operations Center) prend forme via une Single Page Application.

## 5.1 Backlog du Sprint 3
*   Développement de l’interface web avec React JS.
*   Connexion frontend/backend via Axios.
*   Création du tableau de bord de supervision (Dashboard).
*   Affichage des statistiques des antennes (KPIs numériques).
*   Visualisation cartographique du réseau de Mahdia (Leaflet).
*   Gestion des alertes simples (Interface de tickets).

## 5.2 Analyse
### 5.2.1 Diagramme de cas d’utilisation
Superviser les antennes, Consulter les indicateurs, Visualiser les antennes sur la carte.
### 5.2.2 Description du cas d’utilisation : Supervision des antennes
*   **Description** : L'ingénieur se connecte et observe le Dashboard.
*   **Indicateurs surveillés** : Pourcentage d'antennes en alerte, disponibilité globale du réseau, évolution des pannes.
### 5.2.3 Description du cas d’utilisation : Visualisation cartographique
*   **Carte du réseau** : Interface plein écran.
*   **Zones couvertes** : Gouvernorat de Mahdia.
*   **Localisation des antennes** : Représentées par des marqueurs colorés selon leur état de santé.

## 5.3 Conception
### 5.3.1 Diagrammes de séquence
Interface React JS → Intercepteur Axios (Ajout JWT) → API Flask → Base de données → Retour JSON → Mise à jour du *State* React (Re-render virtuel).
### 5.3.2 Diagramme de classes
*   **Antenne, Mesure, Alerte** : Structuration de l'état global React (Context/Props).
### 5.3.3 Schéma relationnel
*   **Tables des mesures et alertes** : Reflétées dans les composants de tableaux de données (`DataTables`) côté front.

## 5.4 Réalisation
### 5.4.1 Architecture logique
*   **Interface React JS** : Divisée en composants, pages, services et styles.
*   **API Flask, PostgreSQL/PostGIS, GeoServer** : En arrière-plan.
### 5.4.2 Développement de l’interface web
*   **Interface d’authentification** : Page de connexion avec gestion de session locale (`localStorage`).
*   **Tableau de bord de supervision** : Affichage graphique moderne (Glassmorphism), icônes Lucide-React.
*   **Gestion des alertes** : Panneau recensant les incidents non résolus avec possibilité d'ajouter des commentaires.
*   **Affichage des statistiques** : Cartes "KPI" en haut de l'écran affichant des données agrégées.
### 5.4.3 Intégration cartographique
*   **Affichage des antennes sur la carte** : Bibliothèque React-Leaflet gérant les tuiles et les marqueurs interactifs (Popups informatifs).
*   **Intégration des couches GeoServer** : Utilisation du composant `WMSTileLayer` pour superposer les couches géospatiales lourdes générées par GeoServer sur le fond de carte léger.
*   **Visualisation géographique des équipements** : Filtrage dynamique (Boutons pour isoler les antennes critiques).

## 5.5 Tests et validation
*   **Tests des interfaces utilisateur** : Vérification de la compatibilité navigateur et de la réactivité (Responsive Design).
*   **Validation du tableau de bord** : Synchronisation correcte des données toutes les 10 secondes (Polling asynchrone).
*   **Validation de l’affichage cartographique** : Mouvement fluide de la carte, affichage des popups sans latence, affichage correct des flux WMS de GeoServer.

## Conclusion
La supervision visuelle est désormais totalement opérationnelle. Le tableau de bord web fonctionnel offre une expérience utilisateur premium, digne des environnements industriels.

---

# CHAPITRE VI : SPRINT 4 – Analyse prédictive et système d’alertes intelligentes

## Introduction
*   **Objectifs du Sprint 4** : Transformer un outil de supervision passif en un outil proactif grâce au Machine Learning.
*   **Intégration de l’intelligence artificielle** : L'IA va agir comme un super-opérateur automatisé.

## 6.1 Backlog du Sprint 4
*   Analyse des données historiques et choix de l'algorithme.
*   Mise en place du modèle Isolation Forest.
*   Développement du module prédictif (`prediction.py`).
*   Détection des anomalies (Scoring).
*   Génération des alertes intelligentes (Explainable AI - `diagnostics.py`).

## 6.2 Analyse
### 6.2.1 Diagramme de cas d’utilisation
Détection d’anomalies (Tâche en arrière-plan), Notification des alertes intelligentes (Action vers l'interface).
### 6.2.2 Description du cas d’utilisation : Détection d’anomalies
*   **Description du processus** : Scrutin périodique de l'ensemble de la télémétrie réseau.
*   **Analyse des données des antennes** : Application d'un modèle non supervisé sur des séries temporelles multivariées (CPU, RAM, Température, Latence).
### 6.2.3 Description du cas d’utilisation : Alertes intelligentes
*   **Notification des opérateurs** : Basculement colorimétrique du tableau de bord.
*   **Affichage des alertes dans le dashboard** : Bannière rouge critique et ajout dans la table des incidents avec explication du problème.

## 6.3 Conception
### 6.3.1 Diagrammes de séquence
Simulateur/Senseur → Base de données → API Flask (Orchestrateur) → Modèle IA (Scikit-Learn) → Retour Score → Base de données (Mise à jour Statut & Création Incident).
### 6.3.2 Diagramme de classes
*   **Anomalie, Modèle IA, Alerte** : Les alertes sont des instances générées par les anomalies détectées par le modèle.
### 6.3.3 Schéma relationnel
*   **Table anomalies** : Intégrée sous forme de `incidents` avec un champ de diagnostic métier.
*   **Relations avec les antennes** : Une antenne peut subir plusieurs incidents chronologiques.

## 6.4 Réalisation
### 6.4.1 Architecture logique
*   **Module IA** : Fichiers `model.py`, `scoring.py`, `diagnostics.py`.
*   **API prédictive** : Fonction `run_ai_prediction()`.
*   **Base PostgreSQL/PostGIS & Interface React JS**.
### 6.4.2 Développement du modèle prédictif
*   **Préparation des données** : Imputation des valeurs manquantes par la médiane pour garantir la fiabilité statistique.
*   **Implémentation Isolation Forest** : Initialisation avec un taux de contamination configuré à 8%. Cet algorithme a été sélectionné pour sa grande efficacité mathématique à "isoler" des points de données aberrants sans nécessiter de données labélisées.
*   **Détection des anomalies** : Génération d'une *decision_function* normalisée de 0 à 100% formant le Score de Risque.
### 6.4.3 Développement des alertes intelligentes
*   **Génération des alertes** : Le module `diagnostics.py` identifie mathématiquement la métrique la plus éloignée de la norme (ex: Température > 65°C) pour rédiger un rapport intelligible.
*   **Affichage des alertes dans le dashboard** : Les antennes critiques apparaissent instantanément sur la carte Leaflet et dans la bannière globale `CriticalAlertBanner`.
*   **Notifications des anomalies** : Création automatique d'un ticket d'incident.

## 6.5 Tests et validation
*   **Validation du modèle IA** : Injection de fausses données extrêmes via notre simulateur ; l'Isolation Forest a réagi avec 100% de précision.
*   **Vérification des anomalies détectées** : Confirmation que le changement d'état "Normal" vers "Critique" écrase correctement les anciens statuts en base.
*   **Validation des alertes intelligentes** : Lecture des rapports générés par l'IA sur l'interface React, confirmant la pertinence de l'analyse causale.

## Conclusion
Le Sprint 4 marque l'accomplissement ultime du projet. L'Intelligence Artificielle est non seulement fonctionnelle mais excelle dans son rôle de détection prédictive, justifiant pleinement la migration vers des outils de NOC de nouvelle génération.

---

# Conclusion générale

Le projet de développement de la plateforme de supervision intelligente **GEO-TÉLÉCOM NOC** pour la Direction Régionale de Mahdia de Tunisie Télécom représente une réponse technologique complète aux défis modernes de l'exploitation des réseaux de télécommunications.

Tout au long de ce Projet de Fin d'Études, nous avons démontré qu'il était possible de transcender la supervision traditionnelle — souvent statique et réactive — en combinant de manière harmonieuse plusieurs domaines d'ingénierie pointus. D'une part, l'intégration des **Systèmes d'Information Géographique (SIG)** via PostGIS et GeoServer offre une maîtrise spatiale inestimable pour localiser et anticiper géographiquement les défaillances. D'autre part, l'intégration d'une **Intelligence Artificielle de Machine Learning (Isolation Forest)** a permis de métamorphoser le rôle de l'ingénieur réseau, le faisant passer de l'analyse de données fastidieuse à la prise de décision stratégique, grâce à des diagnostics prédictifs automatisés.

L'adoption d'une architecture **Microservices conteneurisée avec Docker**, d'un backend performant sous **Flask**, et d'une interface utilisateur réactive en **React.js** confère au système final une stabilité, une sécurité et une ergonomie dignes des meilleurs progiciels de l'industrie. Ce travail de conception holistique prouve que l'automatisation intelligente des réseaux (AIOps) est une réalité technologique concrète, prête à optimiser drastiquement les coûts de maintenance et la Qualité de Service (QoS) d'un opérateur historique.

---

# Perspectives et améliorations

Bien que GEO-TÉLÉCOM NOC soit une plateforme pleinement opérationnelle et performante, elle ouvre la voie à de nombreuses perspectives d'évolution pour s'adapter à une échelle encore plus vaste :

*   **Amélioration de l'IA (Deep Learning)** : La transition de modèles statistiques (Isolation Forest) vers des architectures de réseaux de neurones récurrents (LSTM) permettrait d'analyser les tendances chronologiques (Time-Series) avec une précision accrue, anticipant les pannes plusieurs jours à l'avance.
*   **Notifications intelligentes et multicanales** : L'intégration d'un broker de messages (Kafka/RabbitMQ) couplé à une passerelle SMS/Email permettrait d'alerter les techniciens de terrain instantanément, en fonction de leur proximité géographique avec le sinistre.
*   **Application Mobile** : Une déclinaison de la plateforme en application mobile (React Native ou Flutter) offrirait aux techniciens de terrain une carte interactive hors-ligne et la possibilité de clôturer les incidents directement au pied des pylônes.
*   **Supervision temps réel avancée** : L'intégration de protocoles bidirectionnels via WebSockets permettrait de supprimer les requêtes HTTP cycliques, garantissant un affichage "zéro latence" lors des crises réseau majeures.
*   **Amélioration de la sécurité (Zero Trust)** : L'implémentation de l'authentification multifacteurs (MFA) et d'une gestion cryptographique renforcée pour assurer la totale invulnérabilité des données de supervision.
*   **Scalabilité Cloud** : Pour supporter la charge du réseau national complet de Tunisie Télécom, l'infrastructure pourrait évoluer d'un simple déploiement Docker Compose vers une orchestration Cloud complète gérée par Kubernetes (K8s).
