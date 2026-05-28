# CHAPITRE 3 : SPRINT 1 — BACKEND ET INFRASTRUCTURE

## Introduction du chapitre

Le premier sprint a posé les fondations techniques du projet : API REST Flask, schéma PostgreSQL/PostGIS, authentification JWT et conteneurisation Docker. Sans cette base, les modules frontend et IA ne pourraient pas s'appuyer sur un contrat de données stable. Ce chapitre détaille les objectifs, la conception, la réalisation et les tests du sprint 1.

---

## 3.1 Objectifs du sprint

- Mettre en place le dépôt et l'arborescence `api/`, `dashboard/`, `database/` ;
- Créer le schéma de base et l'initialiser avec les antennes de Mahdia ;
- Implémenter l'authentification JWT ;
- Exposer les endpoints CRUD antennes et incidents ;
- Dockeriser l'ensemble pour un démarrage en une commande.

---

## 3.2 Backlog du sprint 1

| ID | Tâche | Statut |
|----|-------|--------|
| S1-01 | init.sql PostGIS + 121 antennes | Terminé |
| S1-02 | Connexion psycopg2 | Terminé |
| S1-03 | Blueprint auth (/auth/login, /auth/me) | Terminé |
| S1-04 | Blueprint antennes (/antennes) | Terminé |
| S1-05 | Blueprint incidents | Terminé |
| S1-06 | docker-compose.yml | Terminé |
| S1-07 | Healthcheck /health | Terminé |

---

## 3.3 Analyse

Le backend centralise la logique métier et sécurise les accès. Les clients (React, simulateur, Arduino) ne communiquent jamais directement avec PostgreSQL. Ce choix respecte le principe de **séparation des responsabilités** et facilite l'audit des opérations via la couche Flask.

---

## 3.4 Conception

### 3.4.1 Diagramme de classes (backend)

Classes de service implicites organisées par blueprint :

- `auth_routes` : login, logout, me ;
- `antennes_routes` : liste, détail, CRUD, métriques admin ;
- `incidents_routes` : liste, résolution, commentaires ;
- `dashboard_routes` : administration utilisateurs.

### 3.4.2 Modèle relationnel

**Tableau 3.2 — Principales tables PostgreSQL**

| Table | Rôle | Clé |
|-------|------|-----|
| antennes | Référentiel sites radio | id |
| mesures | Historique métriques + IA | id, antenne_id |
| incidents | Tickets réseau | id, antenne_id |
| users | Comptes NOC | id |
| audit_logs | Traçabilité | id |
| messages_chat | Messagerie | id |
| historique_etats | Transitions statut | id |

La table `mesures` conserve les colonnes `statut` et `risk_score` renseignées par le pipeline IA.

### 3.4.3 Architecture backend

```
api/
├── app.py                 # Enregistrement blueprints
├── auth/decorators.py     # token_required, admin_required
├── database/connection.py
├── routes/                # Blueprints REST
├── ia/                    # Module IA (Sprint 3)
└── utils/                 # audit, historique, db_extensions
```

---

## 3.5 Réalisation

### 3.5.1 Backend Flask

L'application Flask enregistre les blueprints au démarrage. Un bootstrap (`_bootstrap_au_demarrage`) initialise les extensions (audit, chat, historique) et remet le réseau en état « propre » pour la démonstration (121 antennes normales, 0 incident ouvert) si `NOC_STARTUP_RESET=1`.

**Authentification JWT :** le login vérifie `password_hash` (Werkzeug), puis encode un payload `{id, username, role, exp}`. Les routes protégées décodent le token via `@token_required`.

**Exemple de décorateur :**

```python
@token_required
def list_incidents():
    # g.current_user disponible
    ...
```

### 3.5.2 API REST (extrait)

**Tableau 3.3 — Endpoints API REST principaux**

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| POST | /auth/login | Authentification |
| GET | /antennes | Liste avec dernière mesure |
| GET | /antennes/:id/mesures | Historique |
| PUT | /antennes/:id/metriques | Injection métriques (admin) |
| GET | /incidents | Liste incidents |
| POST | /incidents/:id/resolve | Résolution |
| GET | /dashboard/summary | KPI dashboard |
| GET | /health | Santé conteneur |

### 3.5.3 PostgreSQL

Le script `database/init.sql` crée les extensions PostGIS, les tables, les index sur `(antenne_id, date_mesure DESC)` et peuple les antennes. La vue `antennes_statut` facilite les requêtes de dernière mesure par antenne.

### 3.5.4 Docker

**Tableau 3.1 — Services Docker Compose**

| Service | Image / build | Port hôte |
|---------|---------------|-----------|
| postgres | postgis/postgis:15-3.4 | 6000 |
| api | ./api/Dockerfile | 7000 |
| frontend | ./dashboard (Nginx) | 3000 |
| simulation | ./simulation | — |

**Figure 3.1 : Schéma de déploiement Docker Compose**

[Insérer schéma : postgres ↔ api ↔ frontend + simulation]

*Source : Réalisation personnelle — docker-compose.yml.*

Le réseau bridge `sig_net` isole les conteneurs. Les volumes nommés assurent la persistance PostgreSQL.

---

## 3.6 Tests

- Test manuel Postman : login, GET /antennes avec Bearer token ;
- Vérification healthcheck après `docker compose up` ;
- Test de charge léger : 121 antennes < 2 s sur machine de développement ;
- Validation des contraintes CHECK sur température et CPU en base.

---

## Conclusion du chapitre 3

Le sprint 1 a livré une API REST opérationnelle, une base PostGIS peuplée et un déploiement Docker reproductible. Cette fondation a débloqué le développement parallèle du frontend (chapitre 4) et du module IA (chapitre 5). Les choix JWT et blueprint Flask se sont révélés adaptés à la taille du projet et aux compétences de l'équipe.

---

*Fin du chapitre 3 — environ 14 pages.*
