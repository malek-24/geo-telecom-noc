# Stack opérationnelle — GEO-TÉLÉCOM NOC

Document de référence aligné sur `docker-compose.yml`.

## Services Docker (4)

| Service      | Port hôte | Rôle                                |
|--------------|-----------|-------------------------------------|
| postgres     | 6000      | PostgreSQL 15 + PostGIS             |
| api          | 7000      | Flask / Gunicorn, REST + IA         |
| simulation   | —         | Mesures synthétiques + cycle IA     |
| frontend     | 3000      | React (build) + Nginx, proxy `/api` |

## Cartographie

- **Frontend** : Leaflet + tuiles OpenStreetMap + marqueurs issus de `GET /antennes`
- **Pas de GeoServer** dans la stack actuelle

## Documentation utile

| Fichier | Contenu |
|---------|---------|
| `../README.md` | Démarrage rapide et structure du projet |
| `DEPLOIEMENT_PFE.md` | Lancement Docker |
| `Guide_Explication_Code_PFE (1).md` | Parcours du code |
| `EXPLICATION_FRONTEND_PFE.md` / `EXPLICATION_BACKEND_PFE.md` | Détails React / Flask |

Les anciens rapports (`rapport_part1.md`, etc.) peuvent mentionner GeoServer ou GeoNetwork : se fier à ce fichier et au `README.md` racine pour la version livrée.
