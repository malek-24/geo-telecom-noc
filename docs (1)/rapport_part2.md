# CHAPITRE 3 : SPRINT 1 — BACKEND & INFRASTRUCTURE

## Introduction

Le Sprint 1 constitue le socle technique de la plateforme. L'objectif est de mettre en place l'infrastructure Docker, la base de données PostgreSQL/PostGIS, l'API REST Flask avec authentification JWT, et les endpoints fondamentaux pour la gestion des antennes et des incidents.

## 3.1 Backlog du Sprint 1

| ID | Tâche | Priorité |
|---|---|---|
| T01 | Création de la structure Docker Compose (5 services) | Haute |
| T02 | Initialisation du schéma PostgreSQL/PostGIS (`init.sql`) | Haute |
| T03 | API Flask — authentification JWT (`/auth/login`, `/auth/me`) | Haute |
| T04 | API Flask — CRUD antennes (`/antennes`, `/antennes/<id>`) | Haute |
| T05 | API Flask — gestion des incidents (`/incidents`) | Haute |
| T06 | API Flask — endpoints dashboard (`/admin/users`) | Moyenne |
| T07 | Seed initial : 120 antennes sur 9 zones de Mahdia | Haute |
| T08 | Configuration GeoServer (WMS/WFS) | Moyenne |

## 3.2 Analyse

### Authentification et gestion des sessions

Le système implémente une authentification **stateless** basée sur JWT. Chaque requête protégée doit inclure un token Bearer dans l'en-tête `Authorization`. Le token est signé avec la clé secrète `pfe-geo-telecom-secret-2026` et expire après une durée configurable.

Le système gère trois rôles distincts avec des permissions granulaires :
- `administrateur` : accès complet à toutes les ressources
- `ingenieur_reseau` : accès lecture/écriture aux données techniques
- `technicien_terrain` : accès consultation et gestion des incidents

### Gestion des antennes

Chaque antenne est identifiée par un ID unique et caractérisée par ses attributs géographiques (latitude, longitude, zone), techniques (type : 4G/5G/Macro...) et son statut courant calculé par l'IA. La vue SQL `antennes_statut` agrège les dernières mesures de chaque antenne pour fournir une source de vérité unique.

## 3.3 Conception

### Modèle de base de données

```
antennes (id, nom, zone, type, latitude, longitude, operateur,
          statut, disponibilite, temperature, cpu, debit, date_mesure, geom)
    │
    │ 1──N
    ▼
mesures (id, antenne_id, temperature, cpu, ram, signal,
         traffic, latence, packet_loss, jitter, disponibilite,
         statut, risk_score, date_mesure)
    │
    │ Vue SQL
    ▼
antennes_statut [DISTINCT ON antenne_id ORDER BY date_mesure DESC]

antennes (id) ──1──N──► incidents (id, antenne_id, titre,
                          type_anomalie, statut, criticite,
                          source_detection, metriques, duree_minutes,
                          date_creation, date_resolution)
                              │
                              │ 1──N
                              ▼
                         commentaires_incidents
                          (id, incident_id, utilisateur_id,
                           utilisateur_nom, role, contenu,
                           statut_validation, etat_resolution)

users (id, username, fullname, email, password_hash,
       role, department, phone, status, last_login)
```

### Architecture Flask — Blueprint Pattern

L'API Flask est organisée en **Blueprints** pour la séparation des responsabilités :

```
api/
├── app.py                 ← Point d'entrée, enregistrement des blueprints
├── auth/
│   └── decorators.py      ← @token_required, @role_required
├── database/
│   └── connection.py      ← connecter_base_de_donnees(), rows_to_dicts()
├── ia/
│   ├── model.py           ← IsolationForest.fit_predict()
│   ├── prediction.py      ← Orchestrateur IA principal
│   ├── scoring.py         ← calculate_risk_score(), determine_statut_final()
│   └── diagnostics.py     ← diagnostiquer_incident()
├── routes/
│   ├── auth_routes.py     ← Blueprint auth_bp
│   ├── antennes_routes.py ← Blueprint network_bp
│   ├── incidents_routes.py← Blueprint incidents_bp
│   ├── reports_routes.py  ← Blueprint reports_bp
│   ├── dashboard_routes.py← Blueprint admin_bp
│   └── ia.py              ← Blueprint ia_bp
└── utils/
    └── globals.py         ← JWT_SECRET, DATABASE_URL, ADMIN_LOGS
```

### Architecture Docker Compose

```yaml
services:
  postgres:    # PostgreSQL 15 + PostGIS 3.4  — port 6000:5432
  api:         # Flask + Gunicorn              — port 7000:5000
  simulation:  # Simulateur Python (schedule)  — interne
  frontend:    # React + Nginx                 — port 3000:80
  geoserver:   # GeoServer 2.25.2              — port 8080:8080
```

Tous les services partagent le réseau bridge `sig_net`. Le service `api` et `simulation` dépendent de `postgres` avec une vérification de santé (`pg_isready`).

## 3.4 Réalisation

### Backend — API Flask

**Endpoint d'authentification** :

```python
# POST /auth/login
payload = {
    "id":       user[0],
    "username": user[1],
    "role":     user[3],
    "exp":      datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
}
token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
return jsonify({"token": token, "username": user[1], "role": user[3]})
```

**Décorateur de protection des routes** :

```python
@token_required   # Vérifie le JWT → injecte g.current_user
@role_required('administrateur')   # Vérifie le rôle
def route_protégée():
    ...
```

**Principaux endpoints REST** :

| Méthode | Route | Description | Auth |
|---|---|---|---|
| POST | `/auth/login` | Connexion, retourne JWT | Non |
| GET | `/auth/me` | Infos utilisateur courant | JWT |
| GET | `/antennes` | Liste des 120 antennes | JWT |
| GET | `/antennes/<id>` | Détail d'une antenne | JWT |
| GET | `/antennes/<id>/history` | Historique des mesures | JWT |
| GET | `/incidents` | Liste des incidents | JWT |
| POST | `/incidents/<id>/resolve` | Résoudre un incident | JWT |
| GET | `/alerts` | Antennes en alerte/critique | JWT |
| GET | `/alerts/critical` | Incidents critiques actifs | JWT |
| GET | `/internal/predict` | Déclencher l'analyse IA | Interne |
| GET | `/admin/users` | Liste des utilisateurs | Admin |
| POST | `/admin/users` | Créer un utilisateur | Admin |
| PUT | `/admin/users/<id>` | Modifier un utilisateur | Admin |
| DELETE | `/admin/users/<id>` | Supprimer un utilisateur | Admin |

### Base de données PostgreSQL/PostGIS

Le schéma est initialisé via `database/init.sql` au premier démarrage du conteneur. L'extension PostGIS permet de stocker les coordonnées GPS dans un champ `geometry(Point, 4326)` :

```sql
CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE antennes (
    id        SERIAL PRIMARY KEY,
    nom       VARCHAR(100) NOT NULL,
    zone      VARCHAR(100) NOT NULL,
    type      VARCHAR(50)  DEFAULT '4G',
    latitude  NUMERIC(9,6) NOT NULL,
    longitude NUMERIC(9,6) NOT NULL,
    statut    VARCHAR(30)  DEFAULT 'normal',
    geom      geometry(Point, 4326)
);
```

La vue `antennes_statut` utilise `DISTINCT ON` pour retourner uniquement la dernière mesure de chaque antenne :

```sql
CREATE VIEW antennes_statut AS
SELECT DISTINCT ON (m.antenne_id)
    a.id, a.nom, a.zone, a.type,
    m.temperature, m.cpu, m.ram, m.latence,
    m.packet_loss, m.disponibilite, m.jitter,
    COALESCE(m.statut, 'en_attente') AS statut,
    COALESCE(m.risk_score, 0) AS risk_score,
    a.latitude, a.longitude, m.date_mesure
FROM antennes a
JOIN mesures m ON a.id = m.antenne_id
ORDER BY m.antenne_id, m.date_mesure DESC;
```

### SIG — GeoServer et PostGIS

GeoServer est configuré pour se connecter à PostgreSQL/PostGIS et exposer la vue `antennes_geo` comme couche cartographique WMS. Cette couche est consommée par Leaflet.js dans le frontend. Les coordonnées de toutes les antennes sont stockées en SRID 4326 (WGS84).

La vue `antennes_geo` est optimisée pour GeoServer :
```sql
CREATE VIEW antennes_geo AS
SELECT a.id, a.nom, a.zone, a.type,
       COALESCE(s.statut, 'normal') AS statut,
       a.geom
FROM antennes a
LEFT JOIN antennes_statut s ON s.id = a.id;
```

### Seed initial — 120 antennes

Le script Python `generate_antennes.py` insère 120 antennes avec des coordonnées GPS réelles dans le gouvernorat de Mahdia, avec une contrainte géographique empêchant de placer des antennes en mer Méditerranée :

```python
# 14 zones géographiques réelles de Mahdia
ZONES = [
    ("Mahdia Centre", 35.504, 11.020, 0.7, 12),
    ("Ksour Essef",   35.414, 10.970, 1.0,  9),
    ("El Jem",        35.292, 10.711, 1.2,  9),
    # ... 11 autres zones
]
```

## Conclusion

Le Sprint 1 a livré une infrastructure robuste et complète : base de données géospatiale, API REST sécurisée par JWT, et 120 antennes géoréférencées. L'architecture Docker garantit la portabilité et la reproductibilité de l'environnement.

---

# CHAPITRE 4 : SPRINT 2 — FRONTEND (REACT.JS)

## Introduction

Le Sprint 2 porte sur la réalisation de l'interface utilisateur. L'objectif est de créer un dashboard moderne, une carte réseau interactive, et des interfaces de gestion des antennes et incidents, avec un contrôle d'accès basé sur les rôles (RBAC).

## 4.1 Backlog du Sprint 2

| ID | Tâche | Priorité |
|---|---|---|
| T09 | Page de connexion (Login.jsx) | Haute |
| T10 | Système RBAC frontend (ProtectedRoute, roles.js) | Haute |
| T11 | Tableau de bord principal (Dashboard.jsx) | Haute |
| T12 | Carte réseau interactive (NetworkMap.jsx + NetworkMap.js) | Haute |
| T13 | Page de gestion des antennes (Antennes.jsx) | Haute |
| T14 | Page des incidents (Incidents.jsx) | Haute |
| T15 | Page d'administration (Admin.jsx) | Moyenne |
| T16 | Page des rapports (Reports.jsx) | Moyenne |
| T17 | Sidebar de navigation contextuelle | Haute |
| T18 | Bannière d'alertes critiques (CriticalAlertBanner.js) | Haute |
| T19 | Chat interne flottant (ChatWidget.js) | Moyenne |

## 4.2 Analyse des besoins utilisateur

Chaque rôle dispose d'une vue adaptée à ses responsabilités :

- **Administrateur** : vision globale, gestion des utilisateurs, logs d'audit, tous les accès
- **Ingénieur Réseau** : focus sur les métriques techniques, historiques, rapports analytiques
- **Technicien Terrain** : consultation du dashboard, gestion des incidents sur le terrain

La navigation est filtrée dynamiquement selon le rôle JWT de l'utilisateur connecté, via la fonction `navForRole(role)` définie dans `roles.js`.

## 4.3 Conception

### Structure des pages React

```
dashboard/src/
├── App.js                    ← Routeur principal (React Router v6)
├── auth/
│   ├── AuthContext.js        ← Context API : estConnecte, token, user
│   ├── roles.js              ← ROLE enum, MENU_NAVIGATION, navForRole()
│   └── AuthContext.js
├── components/
│   ├── ProtectedRoute.js     ← HOC de protection par rôle
│   ├── Sidebar.js            ← Navigation latérale filtrée par rôle
│   ├── NetworkMap.js         ← Composant Leaflet + marqueurs IA
│   ├── CriticalAlertBanner.js← Popup temps réel (incidents critiques)
│   ├── ChatWidget.js         ← Chat interne flottant
│   └── KPI.js                ← Carte KPI réutilisable
├── pages/
│   ├── Login.jsx             ← Page de connexion
│   ├── Dashboard.jsx         ← Tableau de bord principal
│   ├── NetworkMap.jsx        ← Page carte réseau
│   ├── Antennes.jsx          ← Gestion des antennes
│   ├── AntenneHistory.jsx    ← Historique d'une antenne
│   ├── Incidents.jsx         ← Gestion des incidents
│   ├── Reports.jsx           ← Rapports PDF/Excel
│   └── Admin.jsx             ← Administration utilisateurs
└── services/apiConfig.js     ← API_BASE_URL, authCfg (axios)
```

### Système RBAC Frontend

```javascript
// roles.js — Les 3 rôles de la plateforme
export const ROLE = {
  ADMIN:      "administrateur",
  INGENIEUR:  "ingenieur_reseau",
  TECHNICIEN: "technicien_terrain",
};

// Filtrage dynamique du menu par rôle
export function navForRole(role) {
  return MENU_NAVIGATION.filter(lien => lien.roles.includes(role));
}
```

```javascript
// App.js — Protection des routes
<ProtectedRoute roles={[ROLE.ADMIN]}>
  <AdministrationPage />
</ProtectedRoute>
```

### Architecture de routage

| Route | Composant | Rôles autorisés |
|---|---|---|
| `/login` | LoginPage | Tous (non connecté) |
| `/dashboard` | Dashboard | Tous les rôles |
| `/map` | MapPage | Tous les rôles |
| `/equipments` | EquipmentsPage | Tous les rôles |
| `/antenne/:id/history` | AntennaHistoryPage | Tous les rôles |
| `/moderation` | IncidentsPage | Admin, Ingénieur, Technicien |
| `/rapports` | RapportsPage | Admin, Ingénieur |
| `/administration` | AdministrationPage | Admin uniquement |

## 4.4 Réalisation

### Tableau de bord (Dashboard.jsx)

Le dashboard affiche les indicateurs clés en temps réel avec un refresh automatique toutes les 10 secondes :

- **KPIs globaux** : nombre d'antennes normales / en alerte / critiques
- **Métriques moyennes** : CPU moyen, température moyenne, disponibilité
- **Graphique de distribution** : répartition des statuts par zone
- **Liste des incidents actifs** : les 5 derniers incidents en cours

```javascript
// dataRefreshMs.js — Intervalle de rafraîchissement
export const REFRESH_MS = 10_000; // 10 secondes
```

### Carte réseau interactive (NetworkMap.js)

La carte utilise **Leaflet.js** avec des marqueurs colorés selon le statut IA :
- 🟢 Vert : `normal`
- 🟡 Orange : `alerte`
- 🔴 Rouge : `critique`

Chaque marqueur affiche un popup avec les métriques temps réel de l'antenne (CPU, température, latence, disponibilité, risk score).

```javascript
// Couleur du marqueur selon le statut IA
const getColor = (statut) => {
  if (statut === 'critique') return '#ef4444';
  if (statut === 'alerte')   return '#f59e0b';
  return '#22c55e';
};
```

L'intégration GeoServer utilise la couche WMS exposée sur le port 8080 pour afficher les données géospatiales directement depuis PostGIS.

### Gestion des antennes (Antennes.jsx)

La page liste les 120 antennes avec :
- **Filtrage** par zone, type, statut
- **Tri** par CPU, température, risk score
- **Recherche** par nom ou zone
- **Fiche détaillée** : clic → drawer avec toutes les métriques
- **Historique** : lien vers `AntenneHistory.jsx` pour voir l'évolution temporelle

### Gestion des incidents (Incidents.jsx)

Interface de gestion du cycle de vie des incidents :
- Liste des incidents (actifs en premier, puis résolus)
- Badge de criticité coloré (warning / critical)
- Source de détection : `Isolation Forest` (automatique) ou `Manuel`
- Panneau de commentaires : ajout, validation par admin
- Bouton de résolution → appel `PUT /incidents/<id>/resolve`

### Authentification (Login.jsx)

Page de connexion avec :
- Formulaire username/password
- Appel `POST /auth/login` → stockage JWT dans `localStorage`
- Redirection automatique vers `/dashboard`
- Gestion des erreurs (identifiants invalides, compte désactivé)

### Bannière d'alertes critiques (CriticalAlertBanner.js)

Composant global injecté dans `App.js`, actif sur toutes les pages protégées. Il poll l'endpoint `/alerts/critical` toutes les 15 secondes et affiche une bannière animée en cas d'incident critique :

```javascript
// Injecté globalement dans App.js pour tous les utilisateurs connectés
function AppGlobal() {
  const { estConnecte } = useAuth();
  if (!estConnecte) return null;
  return (
    <>
      <CriticalAlertBanner />
      <ChatWidget />
    </>
  );
}
```

### Page d'administration (Admin.jsx)

Interface réservée à l'administrateur :
- **Tableau des utilisateurs** : liste, statut, rôle, dernière connexion
- **Formulaire de création/modification** : username, nom, email, rôle, département, téléphone
- **Activation/désactivation** des comptes
- **Logs d'audit** : 50 dernières actions (connexions, créations, modifications)
- **Paramètres système** : configuration globale de la plateforme

## Conclusion

Le Sprint 2 a livré une interface utilisateur complète, moderne et réactive. Le système RBAC garantit que chaque utilisateur n'accède qu'aux fonctionnalités de son rôle. La carte Leaflet et les tableaux de bord offrent une visualisation en temps réel de l'état du réseau de Mahdia.
