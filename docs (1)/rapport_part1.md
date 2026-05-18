# RAPPORT DE PROJET DE FIN D'ÉTUDES
## Plateforme Intelligente de Supervision des Réseaux Télécoms (GEO-TÉLÉCOM NOC)
**Licence Réseaux & Télécommunications — 2025/2026**
**Auteurs : Malek Maadi & Abir Said**
**Organisme : Tunisie Télécom — Direction Régionale de Mahdia**

---

# INTRODUCTION GÉNÉRALE

## Contexte des réseaux télécoms et des centres NOC

Les réseaux de télécommunications constituent aujourd'hui l'épine dorsale de l'économie numérique. En Tunisie, Tunisie Télécom, principal opérateur national, opère un réseau dense d'équipements actifs couvrant l'ensemble du territoire. La gestion opérationnelle de ces infrastructures est assurée par des centres NOC (Network Operations Center), dont le rôle est de surveiller en permanence l'état du réseau, de détecter les anomalies et d'orchestrer les interventions correctives.

Le gouvernorat de Mahdia, région côtière au potentiel économique et touristique important, dispose d'un parc de 120 antennes réparties sur 14 zones géographiques. Ces équipements, de types 4G, 4G+, 5G, 3G, Macro et Micro, nécessitent une supervision continue pour garantir la qualité de service.

## Problématique

Les centres NOC traditionnels s'appuient sur des outils de supervision réactifs : les techniciens attendent qu'une alarme se déclenche pour intervenir. Cette approche présente des limites majeures : temps de détection long, absence de prédiction des pannes, surcharge d'informations pour les opérateurs, et absence d'exploitation des données historiques. Face à la complexité croissante des réseaux et à la multiplication des équipements, une supervision intelligente et proactive devient indispensable.

## Objectifs du projet

Ce projet vise à développer **GEO-TÉLÉCOM NOC Platform**, une plateforme intelligente de supervision réseau intégrant :

- **Supervision en temps réel** : tableau de bord avec métriques clés (CPU, température, latence, débit, disponibilité)
- **Intelligence artificielle** : détection d'anomalies par l'algorithme Isolation Forest
- **Systèmes d'Information Géographiques (SIG)** : visualisation cartographique des antennes sur Leaflet/GeoServer
- **Gestion des incidents** : cycle complet détection → création automatique → résolution
- **RBAC** : contrôle d'accès basé sur les rôles (administrateur, ingénieur réseau, technicien terrain)

## Méthodologie

Le projet adopte la méthode **Scrum**, avec un développement itératif organisé en 4 sprints :
- **Sprint 1** : Backend Flask, base de données PostgreSQL/PostGIS, infrastructure Docker
- **Sprint 2** : Frontend React.js, dashboard, carte interactive
- **Sprint 3** : Module d'intelligence artificielle (Isolation Forest)
- **Sprint 4** : Simulation IoT, moteur de génération de données temps réel

La modélisation UML est utilisée pour la conception (diagrammes de cas d'utilisation, diagrammes de classes).

## Structure du rapport

Le rapport est organisé en six chapitres suivant la progression des sprints. Le Chapitre 1 présente le cadre général ; le Chapitre 2 détaille la préparation et la capture des besoins ; les Chapitres 3 à 6 couvrent chaque sprint de réalisation.

---

# CHAPITRE 1 : CADRE GÉNÉRAL DU PROJET

## Introduction

Ce chapitre présente le contexte professionnel du projet, analyse l'existant en matière de supervision réseau, identifie ses limites, et expose la solution proposée ainsi que la méthodologie adoptée.

## 1.1 Présentation de l'organisme

### Tunisie Télécom

Tunisie Télécom (TT) est l'opérateur historique de télécommunications en Tunisie, fondé en 1995. Avec un capital de 2,5 milliards de dinars et plus de 8 000 employés, TT offre une gamme complète de services : téléphonie fixe et mobile (2G, 3G, 4G, 5G), Internet ADSL/FTTH, et services aux entreprises. L'opérateur possède l'une des plus denses infrastructures réseau du pays, avec des milliers de sites antennaires couvrant 97% du territoire tunisien.

### Centre de Mahdia

Le centre régional de Tunisie Télécom à Mahdia est responsable de la supervision et de la maintenance du réseau dans le gouvernorat. Il gère un parc de **120 antennes** réparties dans **9 zones géographiques principales** : Mahdia Centre, Hiboun, Ksour Essef, Boumerdes, Chebba, El Jem, Mellouleche, Sidi Alouane et Rejiche.

Les activités principales du centre sont :
- **Supervision réseau** : surveillance 24h/24 des équipements actifs
- **Gestion des incidents** : réception des alarmes, dispatch des techniciens, suivi des résolutions
- **Maintenance préventive** : interventions planifiées sur les sites
- **Reporting** : génération de rapports techniques périodiques

## 1.2 Cadre du projet

### Contexte

La complexification des réseaux mobiles (coexistence 3G/4G/5G), la croissance du trafic de données et la multiplication des équipements rendent la supervision manuelle de plus en plus difficile. Le centre NOC de Mahdia gérait jusqu'ici ses 120 antennes avec des outils classiques, sans capacité prédictive.

### Étude de l'existant

Les outils traditionnels utilisés dans les centres NOC incluent :
- **Systèmes de collecte d'alarmes** : réception des trap SNMP depuis les équipements
- **Tableaux de bord statiques** : affichage d'indicateurs figés, sans analyse contextuelle
- **Logs d'équipements** : fichiers texte analysés manuellement
- **Tickets d'incident manuels** : saisie humaine des pannes détectées

### Critiques de l'existant

| Limitation | Impact |
|---|---|
| Absence d'IA | Pas de détection proactive des anomalies |
| Supervision réactive | Intervention après la panne seulement |
| Pas de SIG | Aucune visualisation géographique du réseau |
| Pas de RBAC | Tous les opérateurs ont le même accès |
| Pas de prédiction | Aucune anticipation des dégradations |

### Solution proposée

**GEO-TÉLÉCOM NOC Platform** est une plateforme web complète qui résout ces limitations grâce à :
- Un **backend REST API** (Flask/Python) exposant toutes les données du réseau
- Un **moteur IA** (Isolation Forest) analysant automatiquement les métriques
- Une **carte SIG interactive** (Leaflet + GeoServer/PostGIS) pour la visualisation
- Un **simulateur IoT** générant des données réseau réalistes toutes les 10 minutes
- Un **dashboard React.js** avec indicateurs temps réel et alertes critiques

## 1.3 Méthodologie

### Méthodes agiles — Scrum

Le projet est développé selon le framework **Scrum**, pour sa flexibilité et son adaptation aux besoins évolutifs. L'équipe est composée de :
- **Product Owner** : définit les besoins et priorise le backlog
- **Scrum Master** : anime les cérémonies et lève les obstacles
- **Équipe de développement** : Malek Maadi & Abir Said

Les cérémonies Scrum appliquées :
- **Sprint Planning** : planification des tâches de chaque sprint (2 semaines)
- **Daily Standup** : synchronisation quotidienne de l'équipe
- **Sprint Review** : démonstration des fonctionnalités au Product Owner
- **Rétrospective** : amélioration continue du processus

### UML

La modélisation UML est utilisée pour :
- **Diagrammes de cas d'utilisation** : interactions acteurs/système
- **Diagrammes de classes** : structure des entités de données
- **Diagrammes de séquence** : flux des processus critiques (authentification, analyse IA)

## Conclusion

Ce chapitre a posé le cadre général du projet en présentant l'organisme d'accueil, les limites de l'existant et la solution proposée. Le chapitre suivant détaille la préparation du projet : capture des besoins, modélisation UML, et planification Scrum.

---

# CHAPITRE 2 : PRÉPARATION DU PROJET

## Introduction

Ce chapitre couvre la phase d'analyse et de préparation : identification des besoins fonctionnels et non fonctionnels, modélisation UML des acteurs et des cas d'utilisation, organisation Scrum, choix de l'environnement technologique et présentation de l'architecture globale.

## 2.1 Capture des besoins

### Besoins fonctionnels

| ID | Fonctionnalité | Description |
|---|---|---|
| BF01 | Authentification | Connexion sécurisée par JWT avec 3 rôles |
| BF02 | Dashboard | KPIs réseau en temps réel (CPU, température, incidents) |
| BF03 | Carte SIG | Visualisation géographique des 120 antennes |
| BF04 | Gestion des antennes | CRUD, historique des métriques, filtrage par zone/type |
| BF05 | Gestion des incidents | Création automatique IA, résolution manuelle, commentaires |
| BF06 | Analyse IA | Détection d'anomalies Isolation Forest, score de risque |
| BF07 | Rapports | Export PDF/Excel des analyses réseau |
| BF08 | Administration | CRUD utilisateurs, logs système, paramètres |
| BF09 | Alertes critiques | Notification temps réel (bannière) pour antennes critiques |
| BF10 | Chat interne | Messagerie entre opérateurs NOC |

### Besoins non fonctionnels

| Catégorie | Exigence |
|---|---|
| **Sécurité** | Authentification JWT, hachage des mots de passe (Werkzeug), RBAC strict |
| **Performance** | Cycle de refresh 10 s (dashboard), analyse IA < 5 s pour 120 antennes |
| **Disponibilité** | Architecture Docker avec `restart: unless-stopped` sur tous les services |
| **Scalabilité** | Architecture microservices, réseau Docker isolé (`sig_net`) |
| **Maintenabilité** | Code structuré en blueprints Flask, composants React réutilisables |

## 2.1.2 Modélisation

### Acteurs du système

| Acteur | Rôle | Pages accessibles |
|---|---|---|
| **Administrateur** | Accès complet, CRUD utilisateurs | Toutes les pages |
| **Ingénieur Réseau** | Supervision technique, rapports | Dashboard, Carte, Antennes, Incidents, Rapports |
| **Technicien Terrain** | Consultation, gestion incidents | Dashboard, Carte, Antennes, Incidents |

### Cas d'utilisation principaux

**UC01 — S'authentifier**
- Acteur : Tout utilisateur
- Précondition : Compte actif en base de données
- Flux : Saisie username/password → vérification hash bcrypt → génération JWT → redirection dashboard
- Exception : Compte désactivé → message d'erreur 403

**UC02 — Consulter le dashboard**
- Acteur : Tous les rôles
- Description : Affichage des KPIs (antennes normales/alerte/critique, CPU moyen, disponibilité)
- Données : Vue `antennes_statut` interrogée toutes les 10 secondes

**UC03 — Visualiser la carte réseau**
- Acteur : Tous les rôles
- Description : Carte Leaflet avec marqueurs colorés selon le statut IA de chaque antenne
- Intégration : Couche WMS GeoServer (`antennes_geo`), popups avec métriques

**UC04 — Déclencher l'analyse IA**
- Acteur : Système (automatique après chaque cycle de simulation)
- Description : Isolation Forest analyse les 8 métriques de chaque antenne
- Résultat : Mise à jour du statut (normal/alerte/critique) et création automatique d'incidents

**UC05 — Gérer les incidents**
- Acteur : Administrateur, Ingénieur, Technicien
- Description : Consulter, commenter et résoudre les incidents créés par l'IA
- Flux résolution : Commentaire "réglé" → statut incident = "resolu" → relancement analyse IA

**UC06 — Administrer les utilisateurs**
- Acteur : Administrateur uniquement
- Description : CRUD complet sur les comptes utilisateurs, activation/désactivation

## 2.2 Scrum

### Équipe Scrum

| Rôle | Personne |
|---|---|
| Product Owner | Encadrant pédagogique |
| Scrum Master | Malek Maadi |
| Développeur Full-Stack | Malek Maadi & Abir Said |

### Product Backlog

| ID | User Story | Priorité | Sprint |
|---|---|---|---|
| US01 | En tant qu'opérateur, je veux me connecter avec mon rôle | Haute | 1 |
| US02 | En tant qu'ingénieur, je veux voir les métriques de chaque antenne | Haute | 1 |
| US03 | En tant qu'admin, je veux gérer les utilisateurs | Haute | 1 |
| US04 | En tant qu'opérateur, je veux voir un dashboard avec les KPIs | Haute | 2 |
| US05 | En tant qu'opérateur, je veux voir les antennes sur une carte | Haute | 2 |
| US06 | En tant qu'ingénieur, je veux que l'IA détecte les anomalies | Haute | 3 |
| US07 | En tant qu'admin, je veux des rapports PDF/Excel | Moyenne | 3 |
| US08 | En tant qu'opérateur, je veux recevoir des alertes critiques en temps réel | Haute | 4 |
| US09 | En tant qu'opérateur, je veux que le système simule le réseau | Haute | 4 |

### Planification des sprints

| Sprint | Durée | Objectif principal |
|---|---|---|
| Sprint 1 | 2 semaines | Backend API, BDD, Docker, authentification |
| Sprint 2 | 2 semaines | Frontend React, dashboard, carte, RBAC UI |
| Sprint 3 | 2 semaines | Isolation Forest, incidents automatiques, rapports |
| Sprint 4 | 2 semaines | Simulateur IoT, alertes critiques, chat interne |

## 2.3 Environnement technologique

### Backend

| Technologie | Version | Usage |
|---|---|---|
| Python | 3.11 | Langage principal |
| Flask | 3.0.3 | Framework API REST |
| Flask-CORS | 4.0.1 | Gestion des requêtes cross-origin |
| Gunicorn | 22.0.0 | Serveur WSGI de production |
| psycopg2-binary | 2.9.9 | Connexion PostgreSQL |
| PyJWT | 2.8.0 | Authentification JSON Web Token |
| Werkzeug | 3.0.3 | Hachage des mots de passe |
| pandas | 2.2.2 | Manipulation des données télécom |
| scikit-learn | 1.5.0 | Modèle Isolation Forest |
| ReportLab | 4.2.0 | Génération de rapports PDF |
| openpyxl | 3.1.5 | Export Excel |

### Base de données

| Technologie | Version | Usage |
|---|---|---|
| PostgreSQL | 15 | Base de données relationnelle |
| PostGIS | 3.4 | Extension géospatiale (coordonnées GPS) |

### Frontend

| Technologie | Version | Usage |
|---|---|---|
| React.js | 18 | Framework SPA |
| React Router | 6 | Navigation côté client |
| Leaflet.js | 1.9 | Carte interactive |
| Nginx | 1.25 | Serveur web de production |

### Infrastructure

| Technologie | Version | Usage |
|---|---|---|
| Docker | 24+ | Conteneurisation des services |
| Docker Compose | 2.x | Orchestration multi-conteneurs |
| GeoServer | 2.25.2 | Serveur cartographique WMS/WFS |
| GeoNetwork | 3.12.12 | Catalogue de métadonnées géographiques |

## 2.4 Architecture globale

La plateforme repose sur une architecture **microservices conteneurisée** composée de 6 services Docker interconnectés via un réseau bridge interne (`sig_net`) :

```
┌─────────────────────────────────────────────────────┐
│                    Utilisateur                       │
└───────────────────────┬─────────────────────────────┘
                        │ HTTP
        ┌───────────────▼──────────────┐
        │    React (Nginx) :3000       │
        └───────────────┬──────────────┘
                        │ REST API
        ┌───────────────▼──────────────┐
        │    Flask API (Gunicorn) :7000│
        └───┬───────────┬──────────────┘
            │           │
┌───────────▼──┐  ┌─────▼────────────┐
│ PostgreSQL/  │  │  Simulation IoT  │
│ PostGIS :6000│  │  (Schedule 10mn) │
└───────────┬──┘  └──────────────────┘
            │
┌───────────▼──────────┐
│ GeoServer :8080      │
│ GeoNetwork :8081     │
└──────────────────────┘
```

**Flux de données** :
1. Le simulateur génère des mesures brutes toutes les **10 minutes** et les insère en base
2. Il déclenche ensuite l'endpoint `/internal/predict` de l'API Flask
3. L'**Isolation Forest** analyse les 8 métriques et calcule le `risk_score` (0-100)
4. Le statut de chaque antenne est mis à jour : `normal` / `alerte` / `critique`
5. Les incidents sont créés/résolus automatiquement selon le statut
6. Le frontend React poll l'API toutes les **10 secondes** pour afficher les données fraîches

## Conclusion

Ce chapitre a établi la base analytique du projet : besoins capturés, acteurs identifiés, backlog priorisé et architecture définie. Les chapitres suivants présentent la réalisation sprint par sprint.
