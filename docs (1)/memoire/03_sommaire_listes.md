## Sommaire (table des matières)

> **Remarque :** en PDF, le sommaire final est généré automatiquement (Pandoc/LaTeX).  
> Ici, on fournit un sommaire indicatif cohérent avec l’organisation par chapitres/sprints.

- Liste des figures  
- Liste des tableaux  
- Liste des abréviations  
- Introduction générale  
- Chapitre 1 : Organisation, contexte et cadrage  
- Chapitre 2 : Analyse des besoins, UML et Scrum  
- Chapitre 3 : Sprint 1 — Backend, BD, SIG, Docker  
- Chapitre 4 : Sprint 2 — Frontend React, cartographie, UI/UX  
- Chapitre 5 : Sprint 3 — Intelligence Artificielle (Isolation Forest)  
- Chapitre 6 : Sprint 4 — Simulation, IoT, temps réel  
- Conclusion générale et perspectives  
- Bibliographie / Webographie  
- Annexes  

---

## Liste des figures (prévisionnelle)

Les figures ci-dessous correspondent à des **captures d’écran** et des **schémas/diagrammes**.  
Dans le rendu final, chaque figure est insérée à l’endroit indiqué dans le chapitre correspondant.

- Figure 1.1 : Organigramme de Tunisie Télécom (simplifié) — [Insérer Capture]
- Figure 1.2 : Localisation du Centre Technique de Mahdia — [Insérer Capture]
- Figure 1.3 : Photo / vue illustrative du centre (ou environnement de supervision) — [Insérer Capture]
- Figure 1.4 : Schéma du flux classique de supervision (avant projet) — [Insérer Schéma]

- Figure 2.1 : Diagramme de cas d’utilisation global — [Insérer Diagramme]
- Figure 2.2 : Diagramme de séquence « Authentification » — [Insérer Diagramme]
- Figure 2.3 : Diagramme de séquence « Traitement d’incident » — [Insérer Diagramme]
- Figure 2.4 : Architecture globale logique (Frontend/Backend/BD/IA/SIG) — [Insérer Schéma]

- Figure 3.1 : Vue Docker Desktop / `docker compose ps` — [Insérer Capture]
- Figure 3.2 : Healthcheck API Flask (`/health`) — [Insérer Capture]
- Figure 3.3 : Exemple de réponse API (`/antennes`) — [Insérer Capture]
- Figure 3.4 : Schéma relationnel de la base PostgreSQL — [Insérer Schéma]
- Figure 3.5 : Exemple de table `mesures` (extrait) — [Insérer Capture]

- Figure 4.1 : Page Login (authentification) — [Insérer Capture]
- Figure 4.2 : Tableau de bord NOC (KPI + incidents + disponibilité) — [Insérer Capture]
- Figure 4.3 : Détail d’un KPI + conventions de couleurs — [Insérer Capture]
- Figure 4.4 : Graphique Recharts (disponibilité 12h) — [Insérer Capture]
- Figure 4.5 : Carte réseau Leaflet (état des antennes) — [Insérer Capture]
- Figure 4.6 : Popup marker (métriques + score IA) — [Insérer Capture]
- Figure 4.7 : Filtres carte (chips) — [Insérer Capture]
- Figure 4.8 : Liste incidents (filtrage + criticité) — [Insérer Capture]
- Figure 4.9 : Page Antennes (table + recherche) — [Insérer Capture]
- Figure 4.10 : Historique d’une antenne — [Insérer Capture]
- Figure 4.11 : Page Rapports — [Insérer Capture]
- Figure 4.12 : Export CSV — [Insérer Capture]
- Figure 4.13 : Journal d’audit — [Insérer Capture]
- Figure 4.14 : Messagerie (widget chat) — [Insérer Capture]
- Figure 4.15 : Messages privés — [Insérer Capture]
- Figure 4.16 : Notification navigateur (nouveau message) — [Insérer Capture]
- Figure 4.17 : Diagramme composants React (haut niveau) — [Insérer Diagramme]
- Figure 4.18 : Diagramme de séquence Frontend ↔ Backend (polling dashboard) — [Insérer Diagramme]

- Figure 5.1 : Schéma du pipeline IA (mesures → features → IF → score → incident) — [Insérer Schéma]
- Figure 5.2 : Architecture IA dans le système (API + BD + simulateur) — [Insérer Schéma]
- Figure 5.3 : Exemple d’injection d’anomalie (`/api/test-ia`) — [Insérer Capture]
- Figure 5.4 : Exemple de sortie `GET /predict` (snapshot IA) — [Insérer Capture]
- Figure 5.5 : Visualisation des sites critiques IA sur dashboard/carte — [Insérer Capture]
- Figure 5.6 : Courbe de distribution des scores (health score) — [Insérer Figure]
- Figure 5.7 : Diagramme de classes (moteur IA) — [Insérer Diagramme]
- Figure 5.8 : Diagramme de séquence « analyse globale simulateur » — [Insérer Diagramme]

- Figure 6.1 : Schéma simulation temps réel (génération → insertion BD → IA → UI) — [Insérer Schéma]
- Figure 6.2 : Architecture IoT (capteurs/Arduino → API → BD → dashboard) — [Insérer Schéma]
- Figure 6.3 : Exemple de métriques simulées (table `mesures`) — [Insérer Capture]

> Total prévisionnel : **40+ figures** (le minimum exigé 35 est dépassé).

---

## Liste des tableaux (prévisionnelle)

- Tableau 1.1 : Présentation synthétique de Tunisie Télécom
- Tableau 1.2 : Fiche descriptive du Centre Technique de Mahdia
- Tableau 1.3 : Analyse critique de l’existant (avant projet)

- Tableau 2.1 : Besoins fonctionnels (liste + priorités)
- Tableau 2.2 : Besoins non fonctionnels (qualité + contraintes)
- Tableau 2.3 : Acteurs du système et rôles (RBAC)
- Tableau 2.4 : Backlog produit (extrait)
- Tableau 2.5 : Planification Sprint 1 (sprint backlog)
- Tableau 2.6 : Planification Sprint 2 (sprint backlog)
- Tableau 2.7 : Planification Sprint 3 (sprint backlog)
- Tableau 2.8 : Matrice traçabilité (besoin ↔ cas d’utilisation ↔ module)

- Tableau 3.1 : Endpoints REST principaux (méthode, URL, description, sécurité)
- Tableau 3.2 : Schéma BD (tables, clés, rôle)
- Tableau 3.3 : Paramètres Docker/Compose (services, ports, volumes)

- Tableau 4.1 : Arborescence des pages React (routes)
- Tableau 4.2 : Principaux composants React (rôle, props, dépendances)
- Tableau 4.3 : Stratégie de rafraîchissement (polling) par page
- Tableau 4.4 : Conventions UI (couleurs/états/alertes)

- Tableau 5.1 : Dictionnaire des variables (métriques supervisées)
- Tableau 5.2 : Comparaison des modèles (RF, SVM, IF) selon critères PFE
- Tableau 5.3 : Hyperparamètres Isolation Forest retenus
- Tableau 5.4 : Seuils de décision (score santé → normal/alerte/critique)
- Tableau 5.5 : Analyse qualitative des résultats (exemples d’anomalies)

- Tableau 6.1 : Scénarios de simulation (normal, surcharge, panne, surchauffe)
- Tableau 6.2 : Événements auditables (action, acteur, objet, justification)

> Total prévisionnel : **20+ tableaux** (le minimum exigé 15 est dépassé).

---

## Liste des abréviations

- **API** : Application Programming Interface  
- **BD** : Base de données  
- **CPU** : Central Processing Unit  
- **CORS** : Cross-Origin Resource Sharing  
- **CSV** : Comma-Separated Values  
- **DevOps** : Development & Operations  
- **GIS / SIG** : Geographic Information System / Système d’Information Géographique  
- **GeoServer** : Serveur cartographique (WMS/WFS)  
- **GPS** : Global Positioning System  
- **HTTP/HTTPS** : HyperText Transfer Protocol (Secure)  
- **IA** : Intelligence Artificielle  
- **IoT** : Internet of Things (Internet des objets)  
- **JWT** : JSON Web Token  
- **KPI** : Key Performance Indicator  
- **NOC** : Network Operations Center  
- **OSM** : OpenStreetMap  
- **PostGIS** : Extension géospatiale PostgreSQL  
- **RBAC** : Role-Based Access Control  
- **REST** : Representational State Transfer  
- **SPA** : Single Page Application  
- **SQL** : Structured Query Language  
- **UML** : Unified Modeling Language  
- **WMS/WFS** : Web Map Service / Web Feature Service  

