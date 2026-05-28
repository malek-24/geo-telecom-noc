## Résumé (Français)

Dans un contexte où les réseaux de télécommunications évoluent rapidement (multiplication des antennes, hétérogénéité des technologies radio, augmentation des volumes de données de supervision), les centres de supervision (**NOC — Network Operations Center**) ont besoin d’outils plus intelligents et plus réactifs pour détecter les incidents, prioriser les interventions et assurer la continuité de service.

Ce mémoire présente la **conception et le développement** d’une plateforme NOC intelligente réalisée au sein de **Tunisie Télécom — Centre Technique de Mahdia**, combinant :

- un **backend** en Python (**Flask**) exposant une **API REST** sécurisée ;
- une base **PostgreSQL/PostGIS** pour stocker les antennes et les mesures réseau ;
- un **frontend** moderne en **React** (TypeScript), intégrant **Tailwind CSS**, **Recharts** et la cartographie **Leaflet/OpenStreetMap** ;
- un module **d’intelligence artificielle** basé sur **Scikit-Learn** et l’algorithme **Isolation Forest** pour la **détection d’anomalies** ;
- une couche **SIG** (Système d’Information Géographique) permettant la visualisation géographique du réseau ;
- un mécanisme de **simulation temps réel** générant des métriques afin de reproduire des scénarios et valider l’ensemble de la chaîne de supervision ;
- des services transverses : **authentification**, **gestion des incidents**, **rapports**, **journal d’audit**, **messagerie interne** et **notifications**.

La méthodologie de réalisation suit une approche **Agile/Scrum**, structurée par sprints : mise en place de l’infrastructure et de l’API, réalisation du tableau de bord React, implémentation du moteur IA, puis intégration de la simulation et des aspects temps réel. Les résultats obtenus montrent qu’une détection proactive, couplée à une visualisation SIG, améliore la lisibilité de l’état réseau et favorise la prise de décision opérationnelle dans un NOC.

**Mots-clés :** NOC, supervision réseau, télécommunications, SIG, Leaflet, OpenStreetMap, Flask, PostgreSQL/PostGIS, IA, Isolation Forest, détection d’anomalies, Scrum, Docker.

---

## Abstract (English)

In modern telecommunications networks, the growth of infrastructure and the diversity of radio technologies increase the complexity of monitoring and incident handling. Network Operations Centers (NOC) require more intelligent and proactive solutions to detect anomalies, prioritize interventions, and ensure service availability.

This thesis presents the design and development of an intelligent NOC platform carried out at **Tunisie Télécom — Mahdia Technical Center**, combining:

- a secured **Flask (Python)** backend exposing a **REST API**;
- **PostgreSQL/PostGIS** for storing antennas and monitoring measurements;
- a modern **React (TypeScript)** frontend with **Tailwind CSS**, **Recharts**, and **Leaflet/OpenStreetMap** mapping;
- an **AI module** based on **Scikit-Learn** and **Isolation Forest** for **anomaly detection**;
- a **GIS layer** for geographical network visualization;
- a **real-time simulation** engine for telemetry generation and scenario validation;
- cross-cutting services such as **authentication**, **incident management**, **reporting**, **audit logging**, **internal messaging**, and **real-time notifications**.

The project follows an **Agile/Scrum** methodology structured into sprints (infrastructure/API, React dashboard, AI engine, simulation and real-time integration). The results suggest that proactive anomaly detection combined with GIS visualization improves network situational awareness and supports NOC decision-making.

**Keywords:** NOC, network monitoring, telecommunications, GIS, Leaflet, OpenStreetMap, Flask, PostgreSQL/PostGIS, AI, Isolation Forest, anomaly detection, Scrum, Docker.

