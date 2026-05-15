# Sprint 1 — Infrastructure et fondations SIG  
## Texte détaillé pour le rapport PFE (sections 3.1 à 3.6)

Ce document décrit **ce que tu dois développer dans ton mémoire** pour le premier sprint : il est aligné sur ton projet réel (`docker-compose.yml`, `database/init.sql`). Tu peux copier-coller des paragraphes dans Word et y ajouter tes **captures d’écran** et **diagrammes**.

---

## 3.1 Objectifs et backlog du sprint

### Objectifs du Sprint 1

Le premier sprint pose les **fondations techniques** de la plateforme de supervision. Sans cette couche, ni l’API, ni le tableau de bord, ni les analyses ultérieures ne peuvent s’appuyer sur des données géographiques cohérentes.

**Objectifs principaux :**

1. **Industrialiser le déploiement** grâce à Docker Compose : tous les services critiques démarrent de la même façon sur une machine de développement ou de démonstration.
2. **Centraliser les données métier** dans une base **PostgreSQL** enrichie par **PostGIS**, avec un schéma clair (antennes, mesures, vues pour la supervision et pour la publication SIG).
3. **Exposer les données spatiales** via **GeoServer** (services standard OGC : WMS / WFS), pour permettre cartographie professionnelle et interopérabilité.
4. **Mettre en place un catalogue de métadonnées** avec **GeoNetwork**, couplé à **Elasticsearch** pour la recherche plein texte dans les fiches.

À la fin du sprint, on doit pouvoir : lancer la stack avec une commande unique, constater que la base `antennes_mahdia` existe avec tables et vues, et accéder aux interfaces GeoServer et GeoNetwork dans le navigateur.

### Backlog du Sprint 1 (exemple rédigé pour le rapport)

| ID | User story / tâche | Description | Critère d’acceptation |
|----|-------------------|-------------|------------------------|
| T1 | En tant que développeur, je veux un fichier Compose à jour | Définir services, réseau, volumes, ports | `docker compose up -d` démarre sans erreur bloquante |
| T2 | Base métier PostGIS | Script `init.sql` monté au premier démarrage | Tables `antennes`, `mesures` et vues créées ; extension `postgis` active |
| T3 | Persistance et santé du SGBD | Volume nommé + healthcheck PostgreSQL | `pg_isready` OK ; données conservées après redémarrage |
| T4 | GeoServer opérationnel | Image officielle/maintenue, lien avec PostGIS | Connexion au store PostGIS ; préparation publication couche (workspace / datastore / layer) |
| T5 | GeoNetwork + dépendances | Postgres catalogue + Elasticsearch | Interface GeoNetwork joignable ; services dépendants « healthy » |
| T6 | Documentation courte | Ports, URLs, identifiants de démo | README ou annexe à jour pour l’équipe / le jury |

### Pourquoi commencer par ce sprint ?

En méthode agile, on livre d’abord une **incrémentation technique stable**. Les sprints suivants (API Flask, React, Grafana) **consomment** cette fondation : même schéma SQL, même réseau Docker, même vue `antennes_geo` pour GeoServer.

---

## 3.2 Docker Compose et réseau `sig_net`

### Rôle de Docker Compose

**Docker Compose** décrit l’ensemble des **services** (conteneurs) du projet dans un fichier YAML (`docker-compose.yml`). Une commande du type `docker compose up -d` :

- télécharge ou construit les images nécessaires ;
- crée les **réseaux** et **volumes** ;
- démarre les conteneurs dans le bon ordre grâce aux dépendances (`depends_on`) et aux **healthchecks**.

**Intérêt pour ton PFE :** reproductibilité (même environnement pour l’encadrant et le jury), isolation des composants, approximation d’un déploiement « micro-services » léger sans orchestrateur Kubernetes.

### Le réseau `sig_net`

Tous les services du projet sont rattachés au réseau Docker **bridge** nommé **`sig_net`**.

**Conséquences pratiques :**

- Chaque conteneur obtient une **adresse IP interne** ; surtout, Docker fournit une **résolution DNS par nom de service**. Par exemple, depuis le conteneur `flask_api`, la base métier est joignable sous le nom d’hôte **`postgres`** (pas `localhost`).
- Les **ports publiés** sur la machine hôte (ex. `5432:5432`, `8081:8080`) permettent d’accéder aux services depuis le navigateur ou des outils externes (pgAdmin, Postman), alors que la communication **entre conteneurs** reste sur le réseau interne.

### Éléments typiques à décrire dans le rapport

1. **Volumes nommés** (`postgres_data`, `geoserver_data`, etc.) : ils assurent la **persistance** des données au-delà du cycle de vie d’un conteneur.
2. **Healthchecks** : PostgreSQL expose `pg_isready` ; Elasticsearch vérifie l’état du cluster (`green` ou `yellow`). Cela permet à des services comme GeoNetwork ou GeoServer de ne démarrer **qu’après** la disponibilité des dépendances (`depends_on` avec `condition: service_healthy`).
3. **Séparation logique** : le fichier Compose regroupe à la fois la base **métier** (`postgres` / PostGIS), la base **catalogue GeoNetwork** (`geonetwork_db`), l’API, le frontend, GeoServer, Grafana, Elasticsearch — ce qui mérite un **schéma de déploiement** dans ton rapport.

### Formulation type pour le mémoire

> « La plateforme est déployée via Docker Compose. L’ensemble des services est attaché au réseau bridge `sig_net`, ce qui permet la résolution DNS interne et une communication sécurisée entre conteneurs sans exposer inutilement les bases sur Internet. Les volumes persistants garantissent la conservation des données SIG et métier entre deux sessions de développement. Les healthchecks sur PostgreSQL et Elasticsearch assurent un ordre de démarrage cohérent pour GeoNetwork et GeoServer. »

*(Ajoute une figure : diagramme des conteneurs et du réseau — tu peux t’inspirer des diagrammes Mermaid dans `docs/architecture_rapport_PFE.md`.)*

---

## 3.3 PostgreSQL / PostGIS

### PostgreSQL comme socle

**PostgreSQL** est le système de gestion de base de données relationnelle choisi pour stocker :

- le **référentiel des antennes** (localisation, zone, type, opérateur) ;
- l’**historique des mesures** de supervision (température, CPU, signal, trafic, horodatage).

La base métier du projet s’appelle **`antennes_mahdia`** (nom défini dans les variables d’environnement du service `postgres`).

### Extension PostGIS

**PostGIS** ajoute à PostgreSQL les types et fonctions **géospatiales** : points, polygones, index spatiaux GIST, fonctions comme `ST_MakePoint`, `ST_SetSRID`.

Dans `init.sql`, l’instruction `CREATE EXTENSION IF NOT EXISTS postgis;` active cette extension **avant** la création des tables géographiques.

### Modèle de données mis en place au Sprint 1

**Table `antennes`**

- Identifiant, nom, zone, type (`fixe` ou `mobile`), latitude et longitude.
- Champ **`geom`** de type `GEOMETRY(Point, 4326)` : le système de référence **4326** correspond au **WGS 84** (lat/lon GPS), standard pour les cartes web.
- Une contrainte **`chk_no_sea`** borne les coordonnées pour rester dans une enveloppe compatible avec le littoral du **gouvernorat de Mahdia** (choix métier / démo du PFE).
- Un **trigger** `trg_antenne_geom` met à jour automatiquement `geom` à partir de `longitude` et `latitude` à chaque insertion ou mise à jour — tu peux expliquer que cela évite les incohérences entre coordonnées numériques et géométrie PostGIS.

**Index**

- Index **GIST** sur `geom` : accélère les requêtes spatiales (filtres, intersections).
- Index sur `zone` : utile pour les filtres par secteur géographique.

**Table `mesures`**

- Lien vers une antenne (`antenne_id`), métriques de supervision.
- Colonne **`statut`** calculée automatiquement (**colonne générée STORED**) selon des seuils sur température et CPU : `normal`, `alerte`, `critique`.  
  → À souligner dans le rapport : la **logique métier** peut vivre en base, ce qui garantit une vision unique pour l’API, GeoServer et Grafana.

**Vues**

- **`antennes_geo`** : pour chaque antenne, **dernière mesure** + géométrie — destinée à la **couche GeoServer** (publication cartographique).
- **`antennes_statut`** : même idée avec `date_mesure` exposée — très utilisée par le **dashboard** et l’API dans les sprints suivants.

### Important pour la rigueur du rapport

La base **`geonetwork`** dans le conteneur **`geonetwork_db`** est **distincte** de `antennes_mahdia`. Elle sert uniquement au **catalogue GeoNetwork**, pas aux mesures des antennes. Cette distinction évite une erreur fréquente dans les mémoires PFE qui fusionnerait à tort les deux rôles.

### Formulation type

> « Le schéma relationnel est déployé automatiquement au premier démarrage du conteneur PostgreSQL grâce au script `database/init.sql`. L’extension PostGIS permet de stocker et d’indexer les positions des antennes. Les mesures sont historisées dans la table `mesures`, avec un statut opérationnel dérivé par la base de données. Les vues `antennes_geo` et `antennes_statut` matérialisent la dernière mesure connue par site, simplifiant à la fois la publication SIG et les futures requêtes applicatives. »

*(Annexe possible : extrait simplifié du script SQL ou tableau « dictionnaire de données ».)*

---

## 3.4 GeoServer

### Rôle de GeoServer dans le projet

**GeoServer** est un serveur cartographique **open source** conforme aux standards **OGC**. Il publie des couches géographiques à partir de sources de données (ici PostGIS) sous forme de services :

- **WMS** (Web Map Service) : images de carte ;
- **WFS** (Web Feature Service) : accès aux objets géographiques et attributs.

Pour ton PFE, GeoServer permet de **professionnaliser** la chaîne SIG : le tableau de bord React peut utiliser Leaflet avec des tuiles ou couches issues de GeoServer, et les métadonnées peuvent référencer les URL de ces services.

### Configuration dans ton dépôt

- Image utilisée : **`kartoza/geoserver:2.23.1`** (version figée pour stabilité du projet).
- Port sur la machine hôte : **8081** → port **8080** dans le conteneur ; interface web souvent sous `http://localhost:8081/geoserver/web`.
- Compte administrateur par défaut du conteneur : défini via **`GEOSERVER_ADMIN_USER`** et **`GEOSERVER_ADMIN_PASSWORD`** dans Compose (valeurs de démonstration à ne pas réutiliser en production).
- Le service **`depends_on`** le service **`postgres`** avec **`condition: service_healthy`** : GeoServer ne démarre qu’une fois la base métier prête.
- Volume **`geoserver_data`** : persistance de la configuration GeoServer (workspaces, styles, caches).

### Ce que tu dois faire manuellement (et mentionner dans le rapport)

GeoServer nécessite généralement une **configuration dans l’interface** :

1. Créer un **workspace** (ex. lié au contexte Mahdia / télécom).
2. Ajouter un **PostGIS datastore** pointant vers le conteneur `postgres`, base `antennes_mahdia`, schéma `public`, utilisateur/mot de passe adaptés au réseau Docker.
3. Publier une **couche** à partir de la vue **`antennes_geo`** (type Point, SRID 4326).

Tu peux documenter ces étapes avec **captures d’écran** (datastore, layer preview).

### Formulation type

> « GeoServer assure la publication standardisée des données spatiales issues de PostGIS. La vue `antennes_geo` agrège la géométrie des antennes avec leurs indicateurs de dernière mesure, ce qui permet de cartographier à la fois la localisation et l’état opérationnel. L’usage de services OGC favorise l’interopérabilité avec d’autres outils SIG et prépare l’intégration avec un catalogue de métadonnées. »

---

## 3.5 GeoNetwork et Elasticsearch

### Rôle de GeoNetwork

**GeoNetwork** est un **catalogue de métadonnées** conforme aux standards internationaux (profils ISO 19115 / INSPIRE selon configuration). Il permet de :

- répertorier les jeux de données et services (dont les couches GeoServer) ;
- faciliter leur **découverte** par recherche ;
- documenter la **qualité**, la **source** et la **responsabilité** des données — enjeu important en géomatique et pour une entreprise comme un opérateur télécom.

### Pourquoi Elasticsearch est présent ?

GeoNetwork **indexe** une partie du contenu du catalogue pour des **recherches rapides** et la recherche plein texte. Dans ta stack, **Elasticsearch 7.17** tourne en **single-node** avec sécurité X-Pack désactivée pour simplifier l’environnement de démo (limitation à signaler dans la conclusion : non adapté tel quel à la production).

### Base PostgreSQL dédiée (`geonetwork_db`)

Le service **`geonetwork_db`** est une instance **PostgreSQL 15 Alpine**, séparée de **`postgres`/PostGIS**.

**À expliquer clairement dans le rapport :**

| Base | Conteneur | Rôle |
|------|-----------|------|
| `antennes_mahdia` | `postgres` (PostGIS) | Données métier : antennes, mesures, vues supervision |
| `geonetwork` | `geonetwork_db` | Persistance interne du catalogue GeoNetwork (utilisateurs catalogue, métadonnées, configuration) |

Cette séparation **isole** le catalogue SIG du référentiel opérationnel et évite les conflits de schéma ou de sauvegarde.

### Démarrage et dépendances

Le service **`geonetwork`** dépend de **`geonetwork_db`** et **`elasticsearch`** avec healthchecks satisfaits — ce qui garantit que le catalogue ne démarre pas « à vide » face à une base ou un index indisponible.

### URL et mise en garde UX

Sur ton déploiement, l’application GeoNetwork est souvent sous **`http://localhost:8080/geonetwork/`**. Une racine `http://localhost:8080/` qui renvoie une erreur peut être **normale** selon l’image ; tu peux le noter pour éviter une fausse impression de dysfonctionnement lors de la soutenance.

### Formulation type

> « GeoNetwork constitue la couche « catalogue » du projet : il centralise les métadonnées décrivant les ressources géographiques et les services publiés. Il s’appuie sur une base PostgreSQL dédiée et sur Elasticsearch pour l’indexation. Cette architecture est distincte de la base métier PostGIS : elle illustre la séparation entre données opérationnelles de supervision et gouvernance documentaire des jeux de données. »

---

## 3.6 Conclusion du Sprint 1

### Bilan

À l’issue du Sprint 1, la plateforme dispose :

- d’un **environnement conteneurisé** reproductible ;
- d’une **base métier géographique** structurée (PostGIS, schéma antennes/mesures, vues pour supervision et SIG) ;
- d’un **serveur de cartographie** GeoServer connecté à cette base ;
- d’un **catalogue GeoNetwork** avec ses dépendances (PostgreSQL catalogue + Elasticsearch).

Ce sprint **ne livre pas encore** l’interface utilisateur métier ni l’API métier complète : il valide la **fondation données + SIG**, indispensable aux itérations suivantes.

### Limites connues (honnêteté scientifique)

- Identifiants et mots de passe **faibles**, destinés à la démo locale.
- Elasticsearch et GeoNetwork configurés pour un **contexte de développement**, pas durcis pour l’Internet public.
- Configuration GeoServer **partiellement manuelle** : à documenter pour la reproductibilité par un tiers.

### Ouverture vers le Sprint 2

Le Sprint 2 pourra s’appuyer sur **`antennes_statut`** et **`mesures`** pour construire l’**API Flask** (`/stats`, `/alerts`, `/antennes`), branchée au même réseau Docker (`postgres` joignable depuis `flask_api`), puis les scripts de **simulation** pour alimenter continuellement les mesures.

---

## Check-list figures pour ton rapport Word

| Section | Figure suggérée |
|---------|------------------|
| 3.2 | Schéma Docker : services + `sig_net` + ports |
| 3.3 | Modèle relationnel ou capture pgAdmin des tables/vues |
| 3.4 | GeoServer : datastore PostGIS + preview couche |
| 3.5 | Navigateur GeoNetwork + schéma GN ↔ ES ↔ DB catalogue |
| 3.6 | Synthèse « avant / après sprint » ou tableau livrables |

---

*Document préparé pour le rapport PFE — projet supervision antennes Mahdia.*
