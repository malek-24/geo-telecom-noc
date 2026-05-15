# Stratégie de Déploiement - Plateforme NOC Tunisie Télécom

Ce rapport détaille la méthodologie utilisée pour déployer la plateforme GEO-TÉLÉCOM, de l'environnement de développement jusqu'à son exposition publique sécurisée pour la phase de recette (démonstration au jury).

## 1. Conteneurisation avec Docker

La plateforme s'appuie intégralement sur **Docker** et **Docker-Compose** afin d'assurer l'homogénéité des environnements (le syndrome du "ça marche sur ma machine" est ainsi éliminé).

Le fichier `docker-compose.yml` orchestre 6 services distincts au sein d'un réseau virtuel privé (`projet-tt_sig_net`) :

- **`postgres`** : Base de données PostgreSQL avec l'extension spatiale PostGIS.
- **`geoserver`** : Serveur cartographique chargé de diffuser les tuiles WMS.
- **`geonetwork`** : Catalogue de métadonnées spatiales.
- **`api`** (Backend) : Conteneur basé sur Python/Flask, exécuté via le serveur WSGI `gunicorn` pour gérer les requêtes concurrentes en production.
- **`simulation`** : Script Python autonome fonctionnant en arrière-plan pour générer la télémétrie réseau synthétique.
- **`frontend`** : Application React optimisée (build de production) servie par un serveur web statique ultra-performant (Nginx).

## 2. Architecture de Proxy Inversé (Reverse Proxy)

Pour simplifier les communications réseau et éviter les problèmes complexes liés à l'origine croisée (CORS), nous avons mis en place une architecture de Reverse Proxy grâce à **Nginx** (intégré au conteneur frontend).

### Configuration Nginx (`nginx.conf`) :
- **Routage Statique** : Toutes les requêtes pointant vers `/` sont redirigées vers `index.html` (comportement indispensable pour le routeur d'une Single Page Application comme React).
- **Routage API** : Nginx intercepte toutes les requêtes contenant le chemin `/api/` et les transfère de manière transparente au conteneur `api` (Flask) sur le port 5000.
- **Mise en Cache** : Nginx a été configuré avec des en-têtes `Cache-Control` stricts. Les fichiers CSS/JS sont mis en cache pendant 7 jours, tandis que le fichier `index.html` ne l'est jamais, garantissant que l'interface utilisateur soit toujours à jour lors des déploiements successifs.

Cette architecture unifie le point d'entrée : le frontend et le backend partagent le même nom de domaine et le même port, simulant ainsi un environnement de production professionnel standard.

## 3. Exposition Publique Sécurisée (Cloudflare Tunnel)

Afin de permettre à un utilisateur externe (ex: encadrant, jury) d'accéder à la plateforme exécutée localement sans avoir à acquérir un nom de domaine payant ni à configurer une redirection de port (Port Forwarding) complexe sur le routeur de l'entreprise, nous avons intégré un **Tunnel Cloudflare** (`cloudflared`).

### Fonctionnement du Tunnel :
1. Un conteneur Docker éphémère `cloudflare/cloudflared` est lancé dans le même réseau privé que l'application.
2. Ce démon établit une connexion sortante (Outbound) sécurisée vers l'infrastructure globale de Cloudflare.
3. Cloudflare génère une URL publique (ex: `https://[nom-aleatoire].trycloudflare.com`) équipée d'un certificat SSL/TLS valide.
4. Lorsqu'un utilisateur distant visite cette URL, Cloudflare relaie la requête au démon local, qui la transmet à son tour au conteneur `frontend` (Nginx) sur le port 80.

### Avantages de cette méthode pour le PFE :
- **Sécurité** : Aucun port entrant n'est ouvert sur la machine hôte. Le pare-feu local reste totalement verrouillé.
- **Chiffrement** : Le trafic entre le navigateur de l'encadrant et Cloudflare est chiffré en HTTPS (SSL/TLS).
- **Simplicité** : Le tunnel masque l'adresse IP publique de la machine hébergeant le projet.
- **Déploiement Continu** : En cas de modification du code, il suffit de recompiler l'image Docker locale. L'encadrant verra les changements instantanément sans que l'URL ne change ou ne se casse.
