# Chapitre 2 — Préparation du projet

## Introduction
La conception d'une plateforme de supervision de l'envergure de GEO-TÉLÉCOM NOC nécessite une phase de préparation rigoureuse afin de traduire la complexité des exigences métier en solutions techniques viables. Ce chapitre décrit les étapes fondatrices du projet, allant de l'analyse détaillée des besoins à la modélisation fonctionnelle, en passant par le choix de la méthodologie de gestion de projet et l'établissement de l'architecture système globale.

## Capture des besoins

### Besoins fonctionnels
La plateforme doit répondre à un ensemble d'exigences opérationnelles visant à simplifier la gestion quotidienne du centre de contrôle du réseau (NOC) :
*   **Supervision en temps réel** : Affichage dynamique des métriques de performance des antennes télécoms (température, charge CPU, disponibilité, latence).
*   **Détection intelligente des anomalies** : Utilisation d'un algorithme de Machine Learning pour analyser les déviations statistiques et générer des alertes autonomes.
*   **Cartographie dynamique (SIG)** : Représentation spatiale des équipements réseau avec une visualisation de leur état de santé en temps réel.
*   **Gestion des incidents** : Création automatique de tickets d'intervention, enrichis par les diagnostics de l'IA, et possibilité d'interaction via des commentaires.
*   **Gestion des rôles et accès** : Contrôle d'accès basé sur les rôles (RBAC) pour segmenter les privilèges des utilisateurs.

### Besoins non fonctionnels
Pour garantir une viabilité en milieu industriel, des exigences techniques strictes ont été définies :
*   **Performance et réactivité** : La plateforme web doit traiter et afficher les données quasi instantanément sans surcharger le navigateur du client (Single Page Application).
*   **Fiabilité et disponibilité** : L'infrastructure logicielle doit être résiliente et facilement déployable (approche par conteneurisation).
*   **Sécurité** : L'authentification doit être robuste (utilisation de JWT) et les mots de passe doivent être chiffrés.
*   **Évolutivité (Scalability)** : L'architecture doit permettre l'ajout futur de nouvelles antennes ou de nouveaux modules prédictifs sans refonte majeure.

## Acteurs et rôles
Afin de refléter l'organisation hiérarchique et opérationnelle de Tunisie Télécom, trois rôles distincts ont été modélisés :
1.  **L'Administrateur** : Super-utilisateur ayant accès à la gestion des comptes, aux paramètres globaux de l'application et à la modération générale.
2.  **L'Ingénieur Réseau** : Utilisateur disposant de privilèges avancés pour l'analyse technique, l'accès à l'historique de télémétrie, la configuration des seuils et la validation des rapports d'incidents.
3.  **Le Technicien Terrain** : Utilisateur axé sur l'opérationnel. Il consulte les alertes sur la carte, intervient sur les antennes défectueuses et met à jour le statut des incidents via des commentaires de résolution.

## Modélisation UML et conception
Afin d'abstraire la complexité du système, nous avons eu recours au langage de modélisation UML.
*   **Diagramme de cas d'utilisation** : Il a permis de cartographier les interactions possibles de chaque acteur avec les différentes briques logicielles (authentification, consultation de la carte, gestion des tickets).
*   **Architecture globale** : Le système a été conceptualisé selon une approche de microservices, séparant distinctement la couche d'accès aux données (PostgreSQL/PostGIS), le moteur de calcul métier (API Flask) et la couche de présentation (React.js).

## Planification Scrum et Backlog Produit
Le développement s'est articulé autour de la méthodologie agile Scrum, reconnue pour sa capacité à gérer les changements et à livrer rapidement de la valeur.
Le projet a été divisé en itérations courtes (Sprints) d'une durée définie, guidées par un Backlog produit priorisé. Les tâches ont été réparties comme suit :
*   **Sprint 1** : Mise en place de l'infrastructure Docker, configuration de la base de données spatiale et des serveurs cartographiques.
*   **Sprint 2** : Développement de l'API RESTful, intégration du modèle de Machine Learning et du simulateur de télémétrie.
*   **Sprint 3** : Conception de l'interface utilisateur, intégration du SIG sur le front-end et assemblage final de la plateforme de supervision.

## Environnement de développement
Pour orchestrer et développer cette solution hybride, plusieurs technologies de pointe ont été sélectionnées :
*   **Docker & Docker Compose** : Pour l'isolation et le déploiement cohérent de l'infrastructure logicielle.
*   **PostgreSQL & PostGIS** : Pour le stockage relationnel et la gestion des objets géographiques.
*   **Python, Flask & Scikit-Learn** : Pour le développement d'une API backend performante et l'intégration scientifique de l'Intelligence Artificielle.
*   **React.js & Leaflet** : Pour la conception d'interfaces utilisateur fluides, modernes et cartographiques.

## Conclusion
Cette phase de préparation a posé les fondations solides indispensables au succès de GEO-TÉLÉCOM NOC. La définition stricte des besoins et le choix assumé d'une stack technologique moderne et conteneurisée ont permis d'entamer la phase de développement avec une vision architecturale claire et sécurisée.

---

# Chapitre 3 — Sprint 1 : Infrastructure et fondations SIG

## Déploiement par conteneurisation
Le premier jalon technique du projet consistait à bâtir une infrastructure logicielle résiliente. Afin d'éviter les problèmes liés aux conflits d'environnements ("ça marche sur ma machine"), nous avons adopté une approche 100% conteneurisée via Docker. Le fichier `docker-compose.yml` a été rédigé pour orchestrer cinq services distincts, tous communiquant de manière isolée et sécurisée via un réseau virtuel dédié nommé `sig_net`.

Cette architecture microservices présente l'avantage d'une évolutivité horizontale : chaque brique (base de données, serveurs SIG, API, Frontend) peut être redémarrée, mise à jour ou dupliquée indépendamment des autres, garantissant ainsi une haute disponibilité.

## Base de données et modélisation géospatiale
Le cœur du stockage des données repose sur PostgreSQL. Pour répondre au besoin de visualisation géographique des équipements, l'extension PostGIS a été activée. 
Les tables relationnelles ont été conçues pour normaliser les données : une table `antennes` pour les métadonnées de l'équipement, une table `antennes_statut` pour l'historique télémétrique, et une table `users` pour l'authentification. 
Une attention particulière a été portée à la création de la vue dynamique `antennes_geo`. Cette abstraction en base de données permet aux serveurs cartographiques d'interroger directement les équipements sous forme de points géométriques (Point geometry), optimisant ainsi les temps de requête.

## L'écosystème SIG (Système d'Information Géographique)
La supervision spatiale est un pilier de l'application. Pour ce faire, nous avons déployé deux outils standards de l'industrie :
1.  **GeoServer** : Connecté directement à notre base PostgreSQL, il agit comme un moteur de rendu. Il transforme la donnée tabulaire en flux cartographiques normalisés (WMS - Web Map Service), prêts à être consommés par le front-end.
2.  **GeoNetwork & Elasticsearch** : Déployés pour la gestion des métadonnées géospatiales et le catalogage, ils préparent le système à une future intégration massive de données réseau (câbles, routeurs, nœuds optiques) tout en offrant des capacités de recherche très hautes performances.

---

# Chapitre 4 — Sprint 2 : API et traitement des données

## Le Backend Flask et l'API REST
Le second Sprint s'est concentré sur la logique métier et le traitement des données. Le framework Python Flask a été choisi pour sa légèreté et sa modularité. L'API a été structurée selon une architecture RESTful stricte, exposant des *endpoints* sécurisés (tels que `/api/stats`, `/api/antennes`, `/api/incidents`) qui agissent comme l'unique point d'entrée pour la manipulation des données.
La sécurité de ces accès est assurée par un système d'authentification par jeton (JSON Web Token - JWT). Des décorateurs personnalisés interrogent la validité du jeton et les droits de l'utilisateur à chaque requête, garantissant l'intégrité du système de gestion des rôles.

## Le moteur d'Intelligence Artificielle
L'innovation majeure de GEO-TÉLÉCOM NOC réside dans sa capacité de diagnostic prédictif. Nous avons implémenté l'algorithme d'**Isolation Forest** (via Scikit-Learn), particulièrement adapté à la détection d'anomalies dans des séries temporelles non étiquetées. Le pipeline IA est isolé dans un sous-module spécifique pour respecter la séparation des préoccupations :
*   **`model.py`** : Il prend en charge l'ingestion des métriques réseau, le nettoyage des données (imputation des valeurs manquantes) et l'entraînement du modèle non supervisé pour isoler les comportements atypiques.
*   **`scoring.py`** : Ce module convertit la "fonction de décision" mathématique complexe de l'IA en un score de risque lisible par l'humain (de 0 à 100 %). Il applique ensuite des règles métier pour définir l'état du système (Normal, Alerte, Critique).
*   **`diagnostics.py` (Explainable AI)** : Afin de lutter contre l'effet "boîte noire" de l'IA, ce script analyse les métriques ayant conduit à l'alerte pour générer dynamiquement un rapport textuel justifiant la prédiction (par exemple : "Déviation majeure causée par une surchauffe à 80°C").
*   **`prediction.py`** : C'est le chef d'orchestre. Il synchronise l'output de l'IA avec la base de données, met à jour le statut des équipements et automatise la création ou la résolution des tickets d'incidents.

## Le simulateur de données
Pour valider l'ensemble de la chaîne de traitement en conditions réelles, un moteur de simulation (`generate_mesures.py`) a été développé. Il injecte de la télémétrie réseau de manière asynchrone, en générant des comportements stochastiques réalistes (variations de charge CPU, pics de latence) et déclenche l'inférence du modèle IA, recréant fidèlement la dynamique d'un centre d'opérations télécom.

---

# Chapitre 5 — Sprint 3 : Dashboard et supervision

## Développement Frontend avec React.js
Le dernier Sprint a été dédié à la concrétisation visuelle du projet. Pour offrir une expérience utilisateur (UX) optimale et sans rechargement de page, la bibliothèque React.js a été exploitée. L'architecture du front-end repose sur des composants réutilisables, facilitant la maintenance du code.

Le cœur applicatif est régi par un routeur intelligent qui intègre la notion de routes protégées (`ProtectedRoute`). Selon le jeton JWT détenu en mémoire locale (Context API), l'interface adapte son contenu : l'ingénieur aura accès aux rapports d'anomalies détaillés, tandis que l'administrateur débloquera le panneau de configuration des utilisateurs.

## Visualisation Temps Réel et KPIs
Le tableau de bord (Dashboard) a été pensé pour offrir une vision macroscopique instantanée de l'état du réseau. Il regroupe des indicateurs clés de performance (KPIs) mis à jour de manière asynchrone, permettant de surveiller le volume global d'antennes affectées par des anomalies de criticité variable. Le design adopte une approche moderne et réactive (Responsive), privilégiant un style épuré et professionnel.

## Intégration SIG et Supervision des Incidents
L'intégration de la bibliothèque **Leaflet** au sein de React a permis la création de la vue Cartographique. Cette carte interroge à la fois notre API pour récupérer l'emplacement et le statut dynamique des antennes, et GeoServer pour afficher les couches WMS de contexte spatial. L'opérateur peut ainsi identifier visuellement et géographiquement les clusters de pannes réseau.

En parallèle, le module de gestion des incidents offre une interface tabulaire où les équipes techniques peuvent consulter les tickets ouverts par l'Intelligence Artificielle, analyser les diagnostics automatisés, et saisir des commentaires d'intervention, clôturant ainsi la boucle d'exploitation NOC.

---

# Chapitre 6 — Tests, validation et difficultés

## Démarche de validation
La mise en production d'une plateforme hybride (Web, SIG, IA) requiert des procédures de tests rigoureuses. 
Sur le plan technique, nous avons simulé des montées en charge via le script d'injection pour observer le comportement de la base de données et les temps de réponse de l'Isolation Forest. L'API REST a fait l'objet de tests d'intégration visant à valider la solidité des requêtes, la gestion des erreurs (statuts HTTP 401, 403, 404, 500) et la stabilité des tokens JWT.
Sur le plan fonctionnel, des parcours utilisateurs complets ont été validés : de l'apparition d'une alerte simulée sur la carte, à sa classification par l'IA, jusqu'à sa résolution par un profil "Ingénieur" sur l'interface React.

## Difficultés rencontrées et solutions apportées
Le développement de ce projet ambitieux a soulevé plusieurs défis techniques majeurs :
*   **Orchestration Docker et Résolution DNS** : L'un des premiers obstacles a été la communication inter-conteneurs. Lors des premières exécutions, le simulateur ne parvenait pas à contacter l'API. La solution a résidé dans la configuration explicite d'un réseau *bridge* (`sig_net`) dans le `docker-compose.yml`, et l'utilisation des noms de conteneurs (`http://api:5000`) comme hôtes DNS internes.
*   **Concurrence d'accès à la base de données** : Le modèle IA, le simulateur et l'API tentaient parfois d'écrire simultanément sur la table des incidents, générant des conflits de transactions. L'implémentation de la fonction `synchroniser_incidents_isolation_forest` a été revue pour centraliser l'écriture, créant ainsi une source de vérité unique (Single Source of Truth).
*   **Effet "Boîte Noire" de l'IA** : L'algorithme d'Isolation Forest se limitait à identifier une ligne de données comme aberrante sans fournir d'explication. Il a fallu investir un effort de recherche considérable pour implémenter un module de diagnostic post-prédiction, capable de comparer les vecteurs de données aux normes attendues pour justifier algorithmiquement la cause de l'alerte.

---

# Conclusion générale

Le projet GEO-TÉLÉCOM NOC s'inscrit dans une réponse directe aux défis contemporains de l'industrie des télécommunications. Face à la prolifération des équipements et à la complexité croissante des réseaux, la simple supervision manuelle atteint ses limites.

À travers ce Projet de Fin d'Études, nous avons démontré avec succès la viabilité d'une architecture moderne orientée microservices. En mariant la puissance d'analyse spatiale des Systèmes d'Information Géographique (PostGIS, GeoServer) aux capacités prédictives du Machine Learning (Isolation Forest), nous avons transformé un processus de monitoring passif en une véritable plateforme d'assistance décisionnelle intelligente et automatisée.

L'application livrée se distingue par sa robustesse back-end, sécurisée et conteneurisée, alliée à une expérience utilisateur front-end (React.js) réactive, fluide et adaptée aux exigences d'un centre d'opérations réseau. Ce travail valide non seulement des compétences avancées en ingénierie logicielle et en intelligence artificielle, mais propose également un outil immédiatement exploitable, répondant aux standards professionnels du marché.

---

# Perspectives et améliorations

Bien que la plateforme soit opérationnelle et stable, plusieurs axes de développement pourraient considérablement enrichir ses capacités lors de futures itérations :

*   **Évolution de l'Intelligence Artificielle (Deep Learning)** : Le passage d'un algorithme classique (Isolation Forest) vers des architectures de réseaux de neurones récurrents (LSTM) permettrait d'analyser la temporalité fine des signaux et d'anticiper les pannes avant même qu'elles ne produisent les premiers symptômes d'alerte.
*   **Notifications Intelligentes et Multicanales** : L'implémentation d'un système de messagerie asynchrone (comme RabbitMQ ou Kafka) couplé à une API de communication permettrait d'envoyer des alertes par SMS ou email aux techniciens en fonction de leur proximité géographique avec l'antenne défectueuse.
*   **Déclinaison en Application Mobile** : Pour les techniciens de terrain, une version mobile native de l'application permettrait une utilisation hors ligne de la carte réseau et la possibilité de clôturer des tickets d'incidents directement au pied de l'antenne, le tout synchronisé à la reconnexion.
*   **Scalabilité Cloud et Haute Disponibilité** : Pour un déploiement à l'échelle nationale impliquant des dizaines de milliers d'antennes, l'infrastructure pourrait être migrée sous un orchestrateur Kubernetes (K8s) hébergé sur le Cloud, offrant une évolutivité dynamique et une tolérance aux pannes maximale.
*   **Sécurité Zéro Confiance (Zero Trust)** : L'ajout de l'authentification multifacteurs (MFA) et de registres d'audit incorruptibles renforcerait davantage la sécurité de l'interface d'administration.
