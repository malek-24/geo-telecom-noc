# Plateforme NOC GEO-Télécom — Tunisie Télécom (Mahdia)

Projet de fin d'études : supervision réseau des antennes avec carte SIG, tableau de bord et détection d'anomalies par intelligence artificielle (Isolation Forest).

## Architecture (4 services Docker)

| Service      | Port | Rôle |
|-------------|------|------|
| **postgres** | 6000 | Base PostgreSQL + PostGIS (antennes, mesures, incidents) |
| **api**      | 7000 | API REST Flask (JSON, JWT, IA) |
| **frontend** | 3000 | Interface React (tableau de bord NOC) |
| **simulation** | — | Génération périodique de mesures (démo / soutenance) |

```text
[React :3000]  ──HTTP──►  [Flask :7000]  ──SQL──►  [PostgreSQL :6000]
                              ▲
                    [simulation] (mesures)
```

## Démarrage rapide

```bash
docker compose up -d --build
```

- Application : http://localhost:3000  
- API (santé) : http://localhost:7000/health  
- Comptes de démo : voir variables `AUTH_*` dans `docker-compose.yml` (ex. admin / admin123)

## Structure du dépôt

```text
PROJET-TT/
├── api/                 # Backend Flask
│   ├── app.py           # Point d'entrée, enregistrement des routes
│   ├── routes/          # Un fichier par domaine (antennes, incidents, admin…)
│   ├── ia/              # Modèle Isolation Forest, scoring, prédiction
│   └── database/        # Connexion PostgreSQL
├── dashboard/           # Frontend React
│   └── src/
│       ├── pages/       # Une page par écran (Dashboard, Carte, Antennes…)
│       ├── components/  # Sidebar, alertes, chat
│       └── services/    # URL API, export CSV
├── database/init.sql    # Schéma et données initiales
├── simulation/          # Scripts de mesures simulées
└── docker-compose.yml
```

## Pages de l'interface

| Route | Fichier | Description |
|-------|---------|-------------|
| `/dashboard` | `pages/Dashboard.jsx` | KPIs, carte réseau (lien), graphique disponibilité 12h, incidents |
| `/map` | `pages/NetworkMap.jsx` | Carte Leaflet + OpenStreetMap + marqueurs antennes |
| `/equipments` | `pages/Antennes.jsx` | Liste / CRUD antennes |
| `/moderation` | `pages/Incidents.jsx` | Incidents et résolution |
| `/rapports` | `pages/Reports.jsx` | Export PDF / Excel |
| `/administration` | `pages/Admin.jsx` | Utilisateurs et paramètres (admin) |

## Carte réseau (sans GeoServer)

Les positions et statuts des antennes sont chargés via **`GET /antennes`** et affichés en **marqueurs Leaflet**. Le fond de carte est **OpenStreetMap**. Aucun serveur cartographique WMS n'est requis.

## Intelligence artificielle (résumé)

1. Les mesures (température, CPU, signal, latence, disponibilité) sont stockées dans `mesures`.
2. Le module `api/ia/` entraîne un **Isolation Forest** et calcule un score de risque.
3. Selon le score, le statut antenne devient `normal`, `alerte` ou `critique` ; un incident peut être créé.

## Documentation détaillée (rapport PFE)

Le dossier `docs (1)/` contient les rapports et guides rédigés pour le mémoire (architecture, déploiement, explication du code).

## Développement local (sans Docker)

**API :**

```bash
cd api
pip install -r requirements.txt
# Configurer DATABASE_URL puis :
python app.py
```

**Frontend :**

```bash
cd dashboard
npm install
npm start
```

Le proxy de développement (`setupProxy.js`) redirige les appels `/api` vers Flask.
