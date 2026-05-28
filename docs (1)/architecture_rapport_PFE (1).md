# Architecture — texte et diagrammes alignés sur le dépôt

Ce fichier décrit l’**architecture opérationnelle actuelle** (code + `docker-compose.yml`).  
Exportez les diagrammes Mermaid via [mermaid.live](https://mermaid.live) si besoin pour le rapport.

> **Stack actuelle (mai 2026)** : 5 services Docker — `postgres`, `api`, `simulation`, `frontend`, `geoserver`. **GeoNetwork** et **Grafana** ne font plus partie du dépôt.

---

## Figure 1 — Schéma d’architecture logique

```mermaid
flowchart TB
  subgraph clients["Navigateur / utilisateur"]
    UI[Dashboard React + Leaflet]
  end

  subgraph edge["Couche exposition"]
    NGX[Nginx - conteneur frontend]
    GS[GeoServer WMS/WFS]
  end

  subgraph app["Couche application"]
    API[API Flask / Gunicorn]
    SIM[Simulation MRRW + IA]
    ML[Isolation Forest - endpoint /predict]
  end

  subgraph data["Couche données"]
    PG[(PostgreSQL + PostGIS\nantennes_mahdia)]
  end

  UI -->|HTTP /api/*| NGX
  NGX -->|proxy| API
  UI -->|HTTP :8080 WMS| GS

  API -->|SQL| PG
  SIM -->|INSERT mesures| PG
  ML --> PG
  GS -->|store PostGIS| PG
```

---

## Figure 2 — Flux de données

```mermaid
sequenceDiagram
  participant Sim as Simulation
  participant PG as PostGIS antennes_mahdia
  participant API as API Flask
  participant React as Dashboard React
  participant GS as GeoServer

  Sim->>PG: INSERT mesures
  PG->>PG: statut (normal/alerte/critique)
  React->>API: GET /stats, /alerts, /antennes (polling)
  API->>PG: Requêtes SQL / vues
  PG-->>API: JSON
  API-->>React: JSON
  React->>React: Carte Leaflet, KPI

  React->>API: GET /predict
  API->>PG: Coordonnées antennes
  API->>API: Isolation Forest
  API-->>React: anomaly 0/1 par site

  GS->>PG: Couches (ex. antennes_geo)
```

---

## Figure 3 — Vue conteneurs Docker

```mermaid
flowchart LR
  subgraph host["Machine hôte - Docker"]
    subgraph net["Réseau : sig_net"]
      postgres[(postgres\nPostGIS)]
      api[flask_api]
      sim[simulation]
      fe[react_app\nnginx]
      gs[geoserver]
    end
  end

  fe -->|proxy /api| api
  api --> postgres
  sim --> postgres
  gs --> postgres
```

**Ports hôte :** 3000 → frontend, 7000 → API, 6000 → PostGIS, 8080 → GeoServer.

---

## Texte — Flux de données (section rapport)

1. **Collecte / simulation** : `simulation/` insère des **mesures** liées aux **antennes** ; le statut est dérivé en base (`init.sql`).
2. **Stockage** : PostGIS (`geom`, SRID 4326), vues `antennes_statut`, `antennes_geo`.
3. **API** : Flask expose JSON (`/antennes`, `/stats`, `/alerts`, `/predict`, incidents, audit…).
4. **Frontend** : React (polling ~60 s), carte Leaflet, couche WMS GeoServer optionnelle.
5. **SIG** : **GeoServer** publie les vues PostGIS ; pas de catalogue GeoNetwork dans la stack actuelle.

---

## Points clés pour la soutenance

- Interface principale : **dashboard React** (port **3000**), API via **`/api`** (nginx → Flask).
- **GeoServer** sur **8080** ; carte en mode dégradé si WMS indisponible.
- Base unique métier : **`antennes_mahdia`** (pas de `geonetwork_db` ni Elasticsearch dans Compose).
