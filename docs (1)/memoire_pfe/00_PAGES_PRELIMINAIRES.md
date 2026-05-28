# MÉMOIRE DE PROJET DE FIN D'ÉTUDES

## LICENCE EN INFORMATIQUE  
### Spécialité : Réseaux et Télécommunications

---

**Titre :** Conception et développement d'une plateforme intelligente de supervision des réseaux télécoms basée sur l'intelligence artificielle et les systèmes d'information géographique (SIG)

**Réalisé par :** Malek Maadi & Abir Said  

**Encadré par :** [Nom de l'encadrant académique]  

**Encadrant professionnel :** [Nom de l'encadrant Tunisie Télécom]  

**Organisme d'accueil :** Tunisie Télécom — Centre Technique de Mahdia  

**Année universitaire :** 2025–2026  

---

## REMERCIEMENTS

Nous tenons à exprimer notre profonde gratitude à toutes les personnes qui ont contribué, de près ou de loin, à la réussite de ce projet de fin d'études.

Nos remerciements s'adressent en premier lieu à l'équipe du **Centre Technique de Mahdia** de Tunisie Télécom, pour l'accueil, la confiance accordée et la mise à disposition des informations nécessaires à la compréhension des enjeux de supervision réseau. Leur expertise terrain nous a permis d'ancrer notre travail dans une problématique professionnelle réelle.

Nous remercions également notre encadrant académique pour ses conseils méthodologiques, ses relectures et son exigence scientifique, qui ont guidé la structuration de ce mémoire.

Enfin, nous adressons nos remerciements à nos familles et à nos enseignants pour leur soutien tout au long de notre parcours en Licence Informatique.

---

## RÉSUMÉ

Les opérateurs télécoms doivent superviser en continu un parc d'infrastructures radio distribuées géographiquement. Les centres d'exploitation réseau (NOC, *Network Operations Center*) s'appuient traditionnellement sur des alarmes et des tableaux de bord statiques, sans capacité prédictive avancée. Ce mémoire présente la conception et le développement d'une **plateforme NOC intelligente** déployée dans le cadre d'un stage PFE au centre de Mahdia.

La solution proposée repose sur une architecture **trois tiers** : une interface web **React**, une API **REST Flask** (Python) et une base **PostgreSQL/PostGIS**. Elle intègre une cartographie **Leaflet/OpenStreetMap**, un moteur de **détection d'anomalies** basé sur **Isolation Forest** (Scikit-learn), une **simulation temps réel** des métriques réseau, ainsi que des modules métiers (incidents, administration, messagerie, journal d'audit, rapports).

Les résultats obtenus montrent une supervision unifiée d'environ **121 antennes** réparties sur le gouvernorat de Mahdia, avec classification automatique des états (normal, alerte, critique), création d'incidents et visualisation cartographique. Le déploiement est assuré par **Docker Compose**, facilitant la reproductibilité et la démonstration en environnement de soutenance.

**Mots-clés :** NOC, télécommunications, supervision réseau, intelligence artificielle, Isolation Forest, SIG, PostGIS, React, Flask, Docker.

---

## ABSTRACT

Telecom operators must continuously supervise geographically distributed radio infrastructure. Network Operations Centers (NOCs) traditionally rely on alarms and static dashboards with limited predictive capabilities. This thesis presents the design and development of an **intelligent NOC platform** implemented during an end-of-study internship at Tunisie Télécom, Mahdia Technical Center.

The solution follows a **three-tier architecture**: a **React** web frontend, a **Flask REST API** (Python), and a **PostgreSQL/PostGIS** database. It integrates **Leaflet/OpenStreetMap** mapping, **Isolation Forest** anomaly detection (Scikit-learn), real-time metric simulation, and business modules (incidents, administration, messaging, audit trail, reports).

Results demonstrate unified supervision of approximately **121 antennas** across Mahdia governorate, with automatic status classification (normal, alert, critical), incident management, and geographic visualization. Deployment uses **Docker Compose** for reproducibility and demonstration.

**Keywords:** NOC, telecommunications, network supervision, artificial intelligence, Isolation Forest, GIS, PostGIS, React, Flask, Docker.

---

## SOMMAIRE

| | Page |
|---|------|
| Remerciements | i |
| Résumé / Abstract | ii |
| Liste des figures | iv |
| Liste des tableaux | vii |
| Liste des abréviations | viii |
| **Introduction générale** | 1 |
| **Chapitre 1 — Cadre général du projet** | 12 |
| **Chapitre 2 — Préparation du projet** | 28 |
| **Chapitre 3 — Sprint 1 : Backend et infrastructure** | 42 |
| **Chapitre 4 — Sprint 2 : Développement frontend** | 58 |
| **Chapitre 5 — Sprint 3 : Intelligence artificielle** | 78 |
| **Chapitre 6 — Sprint 4 : IoT et simulation** | 96 |
| **Conclusion générale** | 108 |
| **Annexes** | 112 |
| **Bibliographie** | 120 |
| **Glossaire** | 122 |

*Les numéros de page sont indicatifs pour une compilation PDF en format A4, police Times New Roman 12 pt, interligne 1,5.*

---

## LISTE DES FIGURES

| Figure | Titre | Page |
|--------|-------|------|
| Figure 0.1 | Architecture globale de la plateforme NOC | 8 |
| Figure 1.1 | Organigramme simplifié de Tunisie Télécom | 14 |
| Figure 1.2 | Localisation du centre technique de Mahdia | 16 |
| Figure 2.1 | Diagramme de cas d'utilisation global | 34 |
| Figure 2.2 | Diagramme de classes simplifié | 38 |
| Figure 2.3 | Architecture logique trois tiers | 40 |
| Figure 3.1 | Schéma de déploiement Docker Compose | 48 |
| Figure 3.2 | Modèle relationnel PostgreSQL (extrait) | 52 |
| Figure 4.1 | Page de connexion — authentification JWT | 60 |
| Figure 4.2 | Tableau de bord NOC — indicateurs KPI | 62 |
| Figure 4.3 | Graphique de disponibilité réseau (12 h) | 64 |
| Figure 4.4 | Cartographie des antennes — vue Mahdia | 66 |
| Figure 4.5 | Liste et tri des antennes supervisées | 68 |
| Figure 4.6 | Fiche détaillée d'une antenne | 70 |
| Figure 4.7 | Interface de gestion des incidents | 72 |
| Figure 4.8 | Résolution d'incident par l'ingénieur | 74 |
| Figure 4.9 | Messagerie interne NOC | 76 |
| Figure 4.10 | Administration — gestion des utilisateurs | 78 |
| Figure 4.11 | Journal d'audit — filtres et export CSV | 80 |
| Figure 4.12 | Module rapports — export PDF/Excel | 82 |
| Figure 4.13 | Bannière d'alerte critique temps réel | 84 |
| Figure 4.14 | Historique métriques d'une antenne | 86 |
| Figure 5.1 | Pipeline IA — de la mesure au statut | 80 |
| Figure 5.2 | Distribution des métriques d'entraînement | 84 |
| Figure 5.3 | Sites en état normal sur la carte | 88 |
| Figure 5.4 | Sites en alerte — marqueur orange | 90 |
| Figure 5.5 | Sites critiques — marqueur rouge pulsant | 92 |
| Figure 5.6 | Résultats IA sur le tableau de bord | 94 |
| Figure 5.7 | Création automatique d'incident IA | 96 |
| Figure 6.1 | Architecture du flux de simulation | 98 |
| Figure 6.2 | Courbe Mean-Reverting Random Walk | 100 |
| Figure 6.3 | Pont série Arduino — antenne ISET | 102 |
| Figure 6.4 | Séquence temporelle des mesures en base | 104 |

*Total : 35 figures — emplacements réservés pour captures d'écran.*

---

## LISTE DES TABLEAUX

| Tableau | Titre | Page |
|---------|-------|------|
| Tableau 1.1 | Comparaison supervision traditionnelle / plateforme proposée | 22 |
| Tableau 2.1 | Besoins fonctionnels priorisés (MoSCoW) | 30 |
| Tableau 2.2 | Besoins non fonctionnels | 32 |
| Tableau 2.3 | Rôles utilisateurs et permissions | 33 |
| Tableau 2.4 | Planification des sprints Scrum | 36 |
| Tableau 3.1 | Services Docker Compose | 46 |
| Tableau 3.2 | Principales tables PostgreSQL | 50 |
| Tableau 3.3 | Endpoints API REST (extrait) | 54 |
| Tableau 4.1 | Structure des composants React | 60 |
| Tableau 4.2 | Intervalles de rafraîchissement automatique | 85 |
| Tableau 5.1 | Variables d'entrée du modèle IA | 82 |
| Tableau 5.2 | Seuils de classification des états | 90 |
| Tableau 5.3 | Paramètres Isolation Forest | 88 |
| Tableau 6.1 | Paramètres de simulation MRRW | 100 |

---

## LISTE DES ABRÉVIATIONS

| Abréviation | Signification |
|-------------|---------------|
| API | Application Programming Interface |
| CRUD | Create, Read, Update, Delete |
| CSV | Comma-Separated Values |
| DHT11 | Capteur numérique température/humidité |
| GPS | Global Positioning System |
| IA | Intelligence artificielle |
| IF | Isolation Forest |
| IoT | Internet of Things |
| JWT | JSON Web Token |
| KPI | Key Performance Indicator |
| MRRW | Mean-Reverting Random Walk |
| NOC | Network Operations Center |
| OSM | OpenStreetMap |
| PFE | Projet de Fin d'Études |
| REST | Representational State Transfer |
| RSSI | Received Signal Strength Indicator |
| SIG | Système d'Information Géographique |
| SQL | Structured Query Language |
| TT | Tunisie Télécom |
| UML | Unified Modeling Language |
