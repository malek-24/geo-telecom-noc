# Stratégie de Déploiement - Plateforme NOC Tunisie Télécom

Ce rapport détaille la méthodologie utilisée pour déployer la plateforme GEO-TÉLÉCOM, de l'environnement de développement jusqu'à son exposition publique sécurisée pour la phase de recette (démonstration au jury).

## 1. Conteneurisation avec Docker

La plateforme s'appuie intégralement sur **Docker** et **Docker-Compose** afin d'assurer l'homogénéité des environnements (le syndrome du "ça marche sur ma machine" est ainsi éliminé).

Le fichier `docker-compose.yml` orchestre **4 services** au sein du réseau `sig_net` :

- **`postgres`** : Base de données PostgreSQL avec l'extension spatiale PostGIS.
- **`api`** (Backend) : Conteneur Python/Flask, exécuté via **Gunicorn** (port hôte **7000**).
- **`simulation`** : Génération de télémétrie réseau synthétique + pont Arduino optionnel.
- **`frontend`** : Application React (build de production) servie par **Nginx** (port hôte **3000**).

La carte SIG utilise **Leaflet** et **OpenStreetMap** ; les antennes sont affichées via l'API (`GET /antennes`), sans serveur WMS séparé.

## 2. Architecture de Proxy Inversé (Reverse Proxy)

Pour simplifier les communications réseau et éviter les problèmes CORS, **Nginx** (intégré au conteneur frontend) assure :

- **Routage statique** : `/` → `index.html` (SPA React).
- **Routage API** : `/api/` → conteneur `api` (Flask, port 5000 interne).
- **Cache** : assets statiques en cache long, `index.html` sans cache.

## 3. Exposition Publique Sécurisée (Cloudflare Tunnel)

Un **tunnel Cloudflare** (`cloudflared`) peut relayer l'application locale vers une URL HTTPS publique, sans ouvrir de ports entrants sur la machine hôte.

### Avantages pour le PFE

- **Sécurité** : pas de port entrant exposé sur le pare-feu local.
- **HTTPS** : certificat géré par Cloudflare.
- **Simplicité** : déploiement local, accès distant pour le jury.
