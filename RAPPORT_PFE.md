# Rapport d'Architecture et d'Implémentation - Plateforme NOC Tunisie Télécom

## 1. Architecture Globale du Système

La plateforme GEO-TÉLÉCOM est conçue selon une architecture de type micro-services, conteneurisée intégralement via Docker pour garantir une haute disponibilité, une isolation des ressources et une facilité de déploiement (Infrastructure-as-Code). 

L'architecture s'articule autour de 6 composants majeurs :

- **Frontend (React.js)** : Une Single Page Application (SPA) offrant une interface de supervision en temps réel (Dashboard, Carte, Incidents). L'application est servie par un serveur Web Nginx léger.
- **Backend API (Flask / Python)** : L'orchestrateur logique. Il expose les API RESTful, gère l'authentification sécurisée (JWT), interroge la base de données et exécute les modèles d'intelligence artificielle.
- **Moteur IA (Isolation Forest)** : Intégré au backend, ce module de Machine Learning non-supervisé détecte les anomalies comportementales du réseau en analysant les corrélations entre la température, le trafic, la latence et le CPU des antennes.
- **Simulateur Réseau (Python / APScheduler)** : Un démon (daemon) indépendant chargé d'injecter des données de télémétrie synthétiques mais réalistes toutes les minutes, simulant ainsi l'activité de 127 antennes relais.
- **Base de Données (PostgreSQL + PostGIS)** : Stockage relationnel et spatial des données (utilisateurs, historiques des mesures, métadonnées des antennes, incidents).
- **Serveur Cartographique (GeoServer)** : Fournit les flux cartographiques WMS/WFS permettant la visualisation géographique des antennes sur la carte Leaflet du Frontend.

## 2. Système de Gestion des Rôles (RBAC)

Pour répondre aux normes de sécurité des Centres de Contrôle du Réseau (NOC), un contrôle d'accès basé sur les rôles (Role-Based Access Control) a été implémenté avec des jetons JWT sécurisés. Le système définit 4 profils distincts :

1. **Administrateur** : Accès total à la plateforme. Gère les utilisateurs (CRUD complet avec hachage bcrypt), valide les commentaires techniques et modifie les configurations système.
2. **Ingénieur Réseau** : Analyse les performances à l'aide des outils de reporting avancés et de l'historique de détection IA.
3. **Modérateur NOC** : Opérateur de salle de contrôle qui surveille la plateforme, assigne les incidents critiques et interagit avec le personnel terrain.
4. **Technicien Terrain** : Accède à la plateforme (généralement via mobile/tablette) pour localiser les équipements en défaut et fournir des retours d'intervention (commentaires techniques).

## 3. Workflow de Résolution des Incidents (Collaboratif)

L'une des innovations majeures du projet est la mise en place d'un flux de travail collaboratif pour le traitement des anomalies réseau :

- **Détection Automatisée** : L'algorithme Isolation Forest détecte une anomalie (ex: surchauffe + perte de paquets) et génère automatiquement un ticket "Incident".
- **Intervention et Traçabilité** : Les techniciens et modérateurs peuvent documenter l'incident via une interface de commentaires techniques. Chaque commentaire reflète l'état de l'intervention (`À régler`, `En cours`, `Réglé`).
- **Validation Hiérarchique** : Les commentaires soumis nécessitent une validation de l'administrateur, assurant la qualité des données de maintenance.
- **Auto-Guérison (Self-Healing state)** : Lorsqu'un technicien déclare un incident comme `Réglé`, le système met immédiatement à jour le statut du réseau en base de données et déclenche un recalibrage asynchrone du modèle IA pour actualiser l'état de santé de l'antenne sur la carte.

## 4. Modernisation UI / UX (Design System)

L'interface graphique a été entièrement repensée selon un design system moderne (inspiré des outils SaaS contemporains comme Linear ou Notion) :
- **Palette Visuelle** : Utilisation d'un thème bicolore (Indigo et Slate) maximisant le contraste et réduisant la fatigue visuelle des opérateurs NOC.
- **Réactivité** : Actualisation asynchrone (Ajax/Axios) toutes les 30 secondes sans rechargement de page.
- **Micro-interactions** : Retour visuel immédiat (animations de validation, spinners de chargement, badges de criticité dynamiques) pour une meilleure fluidité opérationnelle.
