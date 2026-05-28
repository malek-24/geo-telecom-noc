## Introduction générale

### Contexte : évolution des réseaux télécoms et besoin de supervision

Les réseaux de télécommunications modernes constituent une infrastructure critique : ils assurent les communications voix et données, soutiennent les services numériques, et participent directement à la continuité d’activité des entreprises et des administrations. Dans le contexte tunisien, les opérateurs télécoms gèrent des réseaux à large couverture géographique, avec des équipements distribués (antennes, routeurs, alimentations, liaisons de transmission), des contraintes environnementales (température, humidité, conditions électriques) et des attentes élevées des utilisateurs finaux (débit, latence, disponibilité).

En pratique, l’exploitation d’un réseau télécom ne se limite pas au déploiement d’équipements. Elle repose sur une **surveillance continue** (monitoring), une collecte de métriques, la corrélation d’alarmes et la gestion opérationnelle des incidents. Plus le réseau grandit, plus les données deviennent volumineuses et difficiles à interpréter, ce qui rend la supervision manuelle inefficace. Les équipes doivent donc s’appuyer sur des plateformes capables de présenter une vision synthétique, de détecter rapidement les dégradations et d’aider à la priorisation des interventions.

### Rôle des centres NOC (Network Operations Center)

Un centre NOC est un environnement opérationnel où des ingénieurs et techniciens surveillent l’état du réseau. Ses missions principales incluent :

- **Surveillance temps réel** des indicateurs et des alarmes (disponibilité, latence, charge, température, etc.) ;
- **Détection et qualification** des anomalies (incident localisé, incident de zone, panne de transmission, etc.) ;
- **Priorisation** selon la criticité (nombre d’abonnés impactés, service critique, redondance, durée) ;
- **Coordination** avec les équipes terrain et les équipes de maintenance ;
- **Traçabilité** via un journal d’actions (audit) et des rapports.

Dans la réalité, le NOC doit répondre à un double enjeu : d’une part, réduire le temps moyen de détection et de résolution (MTTD/MTTR), et d’autre part, limiter les fausses alertes et la surcharge informationnelle. Ce deuxième point est essentiel car une plateforme de supervision inefficace peut conduire à une fatigue d’alerte (“alert fatigue”), où les opérateurs finissent par ignorer certains signaux.

### Complexité des réseaux modernes : pannes, incidents et limites du monitoring classique

Les incidents réseau peuvent provenir de plusieurs facteurs :

- défaillance matérielle (alimentation, module radio, ventilation) ;
- surcharge CPU ou saturation de ressources ;
- interférences radio ou dégradation du signal ;
- coupure de liaison, congestion, latence élevée ;
- conditions environnementales (température, surchauffe) ;
- erreurs de configuration ;
- opérations de maintenance planifiées.

Les approches classiques de monitoring (liste d’alarmes, logs, seuils fixes) présentent des limites :

- elles sont souvent **réactives** : l’alerte apparaît après la dégradation ;
- elles génèrent beaucoup de **bruit** : un seuil mal calibré peut créer des alertes inutiles ;
- elles ont du mal à intégrer le **contexte géographique** : plusieurs incidents proches peuvent relever d’un même problème de zone ;
- elles n’exploitent pas efficacement l’historique et les patterns (tendance, dérive lente).

Ces limites justifient l’intégration d’approches plus intelligentes, basées sur les données et capables d’apprendre des comportements “normaux” pour détecter des écarts.

### Apport de l’intelligence artificielle dans la supervision

L’intelligence artificielle (IA), et en particulier l’apprentissage automatique (Machine Learning), peut contribuer à :

- **détection d’anomalies** : identifier des comportements atypiques sans définir explicitement tous les seuils ;
- **scoring de risque** : fournir un indicateur de santé et de criticité ;
- **réduction des faux positifs** via des mécanismes d’ajustement et de validation ;
- **explicabilité opérationnelle** : proposer un diagnostic probable (“surchauffe”, “latence anormale”, etc.) ;
- **priorisation automatique** et aide à la décision.

Dans le cadre de ce PFE, le choix s’oriente vers un algorithme non supervisé, **Isolation Forest**, adapté lorsque les données labellisées (anomalie/non-anomalie) sont rares ou difficiles à obtenir dans un contexte réel.

### Apport des SIG (Systèmes d’Information Géographique)

Dans un réseau télécom, la dimension géographique est fondamentale : les antennes sont distribuées sur le territoire, et les incidents peuvent être corrélés à des zones (quartier, délégation, gouvernorat), à une topologie de transmission, ou à des conditions locales. Les SIG apportent :

- une **visualisation intuitive** (carte) ;
- une **corrélation spatiale** (anomalies proches) ;
- une aide au **dispatching** des équipes terrain ;
- une intégration avec des couches cartographiques (OpenStreetMap, couches GeoServer).

L’intérêt principal est de passer d’une supervision uniquement tabulaire à une supervision **contextualisée spatialement**, ce qui améliore la compréhension et la rapidité de décision.

### Problématique

À partir de l’observation de l’existant et des besoins d’un centre technique, la problématique peut être formulée ainsi :

> **Comment concevoir et développer une plateforme NOC intelligente capable de superviser un réseau d’antennes télécoms en temps réel, de visualiser les équipements sur une carte, de gérer les incidents et d’intégrer une détection d’anomalies par IA, tout en garantissant la sécurité, la traçabilité et la facilité d’utilisation ?**

Cette problématique est déclinée en sous-questions :

- comment structurer les données (antennes, mesures, incidents) en base PostgreSQL/PostGIS ?
- comment assurer une API REST sécurisée et robuste (Flask, JWT, RBAC) ?
- comment construire une interface NOC moderne (React, Recharts, Leaflet) avec rafraîchissement temps réel ?
- comment concevoir un pipeline IA opérationnel (prétraitement, entraînement, scoring, intégration BD) ?
- comment valider le système en l’absence de données réelles (simulation temps réel, scénarios de panne) ?

### Objectifs du projet

Le projet vise à réaliser une plateforme complète offrant :

- **supervision des antennes** (statut, métriques, historique) ;
- **monitoring temps réel** avec rafraîchissement périodique ;
- **gestion des incidents** (création, suivi, résolution, criticité) ;
- **visualisation géographique** via carte Leaflet/OpenStreetMap ;
- **analyse des métriques** et tableaux de bord (KPI, courbes) ;
- **détection d’anomalies IA** (Isolation Forest) + score de risque ;
- **simulation** de métriques et scénarios anormaux (démonstration jury) ;
- **administration** (utilisateurs, rôles, antennes) ;
- **rapports** et export (CSV) ;
- **journal d’audit** (traçabilité) ;
- **messagerie interne** et notifications (chat public/privé).

### Méthodologie de réalisation : Agile, Scrum et UML

La conduite du projet suit une méthodologie **Agile** (Scrum), qui permet :

- un découpage en **sprints** avec objectifs mesurables ;
- une intégration incrémentale (backend → frontend → IA → simulation) ;
- une validation régulière avec les parties prenantes ;
- une adaptation progressive aux contraintes.

La modélisation UML est utilisée comme support de conception et de communication :

- diagrammes de cas d’utilisation (vision fonctionnelle) ;
- diagrammes de classes (structure) ;
- diagrammes de séquence (scénarios) ;
- diagrammes de déploiement (infrastructure Docker).

### Organisation du mémoire

Le mémoire est structuré en chapitres cohérents :

- **Chapitre 1** : présentation de l’organisme d’accueil, contexte et cadrage.
- **Chapitre 2** : analyse des besoins, conception UML, Scrum et architecture globale.
- **Chapitre 3 (Sprint 1)** : réalisation du backend, base de données, SIG et déploiement Docker.
- **Chapitre 4 (Sprint 2)** : réalisation du frontend React, UI/UX, cartographie et intégrations.
- **Chapitre 5 (Sprint 3)** : conception et réalisation du moteur IA, intégration et résultats.
- **Chapitre 6 (Sprint 4)** : simulation temps réel, flux IoT et mécanismes temps réel.
- **Conclusion** : bilan, compétences, difficultés, perspectives.

---

## Conclusion de l’introduction générale

L’évolution des réseaux télécoms impose une supervision plus intelligente, associant des capacités d’analyse automatique et des outils de visualisation avancés. Dans ce cadre, l’objectif de ce PFE est de proposer une plateforme NOC intégrée, combinant une API robuste, une interface ergonomique et un module IA de détection d’anomalies, tout en mettant en avant le rôle des SIG pour renforcer la compréhension spatiale de l’état réseau. Le chapitre suivant présente le contexte institutionnel (Tunisie Télécom, Centre Technique de Mahdia) ainsi que le cadrage du projet.

