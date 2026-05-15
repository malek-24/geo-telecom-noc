# Guide d’explication du code — Plateforme SIG (Mahdia)

> **Lecture dans Cursor :** utilisez ce fichier `.md` (aperçu ou éditeur).  
> **Microsoft Word :** ouvrez `Guide_Explication_Code_PFE.docx` depuis l’Explorateur Windows (clic droit → *Ouvrir avec* → Word). L’éditeur Cursor/VS Code **ne sait pas** afficher les `.docx` comme un document : ce n’est pas un bug de votre projet.

Document de travail pour comprendre et présenter le projet technique. Il décrit l’architecture réelle du dépôt (backend, base de données, frontend, Docker).

---

## 1. Vue d’ensemble

Le projet est une plateforme de supervision : des antennes (données géographiques et métier) sont stockées dans **PostgreSQL/PostGIS** ; une **API Flask** expose ces données en **JSON** ; un **tableau de bord React** affiche cartes, indicateurs et alertes ; des services SIG (**GeoServer**, **GeoNetwork**) complètent la chaîne pour publication et métadonnées.

- **Données :** tables `antennes` + `mesures`, vues pour le dashboard et GeoServer.
- **Temps quasi réel :** le frontend interroge l’API toutes les **60 secondes** (polling).
- **Analyse :** endpoint `/predict` avec **Isolation Forest** sur les coordonnées (détection d’anomalies spatiales).

### Arborescence utile du dépôt

```
PROJET-PFE-TT/
├── api/app.py              → API REST Flask
├── database/init.sql       → Schéma PostGIS, tables, vues, trigger géométrie
├── dashboard/src/          → Application React (pages, composants)
├── simulation/             → Scripts de génération / simulation des mesures
├── docker-compose.yml      → Orchestration de tous les services
└── docs/                   → Documentation et guides
```

---

## 3. Docker Compose : rôle de chaque service

Le fichier `docker-compose.yml` lance l’écosystème complet.

- **postgres :** PostGIS, base applicative `antennes_mahdia` (données du dashboard).
- **api :** conteneur Flask (Gunicorn), variable `DATABASE_URL` vers postgres.
- **frontend :** build React puis nginx ; port hôte **3000** → port **80** du conteneur ; les appels API passent par **`/api`** proxifié vers Flask.
- **geoserver :** couches cartographiques WMS/WFS ; URL web **http://localhost:8081/geoserver/web** (admin / geoserver).
- **geonetwork** + **geonetwork_db** + **elasticsearch :** catalogue de métadonnées ; URL **http://localhost:8080/geonetwork/** (la racine `:8080` renvoie 404, c’est normal).
- **grafana :** tableaux de bord optionnels sur le port **3001**.

**Pourquoi `/api` côté navigateur ?** Dans Docker, le navigateur ne doit pas appeler `localhost:5000` pour joindre Flask dans un autre conteneur de la même façon en production. **Nginx** sert le site et redirige `/api/stats` vers le service `api`. La variable `REACT_APP_API_URL=/api` est fixée au **build** Docker du dashboard.

---

## 4. Base de données (`database/init.sql`)

### 4.1 Table `antennes`

Stocke l’identité de chaque site : nom, zone, type (fixe/mobile), latitude, longitude. Le champ `geom` est de type **GEOMETRY(Point, 4326)** — repère GPS WGS84, standard pour Leaflet et GeoServer.

**Contrainte métier :** un `CHECK` évite de placer des antennes en mer (limites longitude/latitude par bande pour Mahdia).

### 4.2 Trigger `update_antenne_geom`

À chaque INSERT ou UPDATE, le trigger recalcule `geom` à partir de longitude/latitude avec `ST_MakePoint` et `ST_SetSRID`. Vous n’avez pas besoin de remplir `geom` à la main.

### 4.3 Table `mesures`

Historique des relevés : température, CPU, signal, trafic. La colonne **statut** est calculée automatiquement (**GENERATED STORED**) : seuils sur température et CPU → `normal`, `alerte` ou `critique`.

### 4.4 Vues `antennes_geo` et `antennes_statut`

- **antennes_geo :** dernière mesure + géométrie — utilisée par **GeoServer**.
- **antennes_statut :** dernière mesure avec `date_mesure` — utilisée par l’API `/antennes` et `/alerts` pour React.

Les deux vues utilisent **JOIN LATERAL** pour ne prendre que la **mesure la plus récente** par antenne.

---

## 5. API Flask (`api/app.py`)

**Flask** + **CORS** : autorise le navigateur à appeler l’API depuis un autre port. Derrière nginx, les requêtes viennent souvent du même site (moins de soucis CORS).

### 5.1 Connexion `get_conn()`

Boucle de tentatives (par défaut 15 fois, pause 2 s) : au démarrage Docker, PostgreSQL peut encore s’initialiser. Sans cela, l’API échouerait au premier appel.

### 5.2 Routes HTTP

| Méthode / chemin | Rôle | Détail |
|------------------|------|--------|
| GET `/` | Santé | Réponse « API OK » — healthchecks Docker. |
| GET `/stats` | Indicateurs | Comptages : total antennes, normal, alerte, critique, zones. |
| GET `/alerts` | Alertes | Lignes `antennes_statut` en critique ou alerte (max 50). |
| GET `/antennes` | Carte / liste | Joint `antennes_statut` + `antennes` (lat/lon + métriques). |
| GET `/predict` | IA | `IsolationForest` sur lat/lon ; `anomaly=1` si outlier. |

### 5.3 `/predict` et Isolation Forest

Le modèle `sklearn.ensemble.IsolationForest` s’entraîne sur les coordonnées de toutes les antennes. Les points anormaux reçoivent le label -1 (converti en `anomaly=1` dans le JSON). Ce n’est **pas** un simple seuil sur la température : c’est une détection de position **atypique** dans le nuage de points.

**Phrase possible au jury :** *« J’utilise Isolation Forest pour repérer des sites géographiquement incohérents ou isolés par rapport au maillage habituel, en complément des seuils métier température/CPU dans la base. »*

---

## 6. Simulation (`simulation/`)

Scripts Python qui alimentent les données de démonstration.

### 6.1 `generate_mesures.py`

Boucle qui insère périodiquement des mesures (température corrélée au CPU + bruit). L’intervalle est défini par **`INTERVAL`** (souvent 60 secondes). Le **statut** de chaque ligne est recalculé par la base (colonne générée).

### 6.2 `generate_antennes.py`

Peuple `antennes` avec des sites réalistes (contrainte côte / terre).

---

## 7. Frontend React (`dashboard/src`)

### 7.1 Point d’entrée

- **index.js :** racine React, styles globaux, Leaflet.
- **App.js :** `react-router-dom` ; `/` → `/dashboard`. Pages : Dashboard, MapPage, EquipmentsPage, AnalyticsPage.

### 7.2 `apiConfig.js`

`API_BASE_URL` lit `REACT_APP_API_URL`. En dev, `.env.development` peut fixer `/api` et **`setupProxy.js`** transmet vers Flask sur le port 5000 de la machine hôte.

### 7.3 `Dashboard.js`

`useEffect` charge `/stats` et `/alerts` au montage puis toutes les 60 secondes. KPI, `NetworkMap`, liste d’alertes ; bandeau en cas d’erreur réseau.

### 7.4 `NetworkMap.js`

- Récupère `/antennes`, marqueurs Leaflet (couleurs selon statut).
- Arbre couvrant minimal (**Prim**) entre les points pour visualiser un « backbone » fibre.
- Panneau type chat : règles sur les données chargées (pas de LLM externe).

### 7.5 Autres pages

- **EquipmentsPage :** `/antennes`.
- **AnalyticsPage :** `/predict`, affichage `anomaly === 1`.
- **Sidebar / Topbar :** navigation et en-tête.

---

## 8. Chaîne de données (schéma pour l’oral)

```
[Simulation / SQL] → mesures + vues antennes_statut
          ↓
[Flask /antennes /stats /alerts /predict]
          ↓ JSON
[React : polling 60 s]
          ↓
[Carte Leaflet + tableaux + KPI]

Parallèle : antennes_geo → GeoServer → WMS/WFS
            métadonnées → GeoNetwork + Elasticsearch
```

---

## 9. Questions fréquentes (jury)

**Pourquoi PostGIS ?**  
Pour stocker des points géographiques, indexer spatialement et publier des couches compatibles SIG.

**Temps réel ?**  
Polling 60 s ; pas de WebSocket dans cette version — choix simple pour de la supervision.

**Différence statut SQL vs anomaly IA ?**  
Le statut vient des règles température/CPU. L’IA sur `/predict` porte surtout sur la **géométrie** du nuage de points.

**Sécurité en production ?**  
Mots de passe par défaut à changer, HTTPS, authentification applicative à prévoir.

---

*— Fin du guide —*
