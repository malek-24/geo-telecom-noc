## Conclusion générale et perspectives

### Bilan du projet

Ce projet de fin d’études, réalisé au sein de **Tunisie Télécom — Centre Technique de Mahdia**, avait pour objectif de concevoir et développer une **plateforme NOC intelligente** combinant supervision réseau, cartographie SIG, gestion d’incidents et détection d’anomalies par intelligence artificielle.

Au terme du travail, les résultats majeurs peuvent être résumés comme suit :

- **Plateforme intégrée** : une chaîne complète “données → traitement → visualisation” a été mise en place (PostgreSQL/PostGIS, API Flask, frontend React, IA, simulation).
- **Supervision opérationnelle** : le dashboard fournit des KPI pertinents (disponibilité, sites critiques/alertes, score IA) et une liste d’incidents actifs.
- **Dimension SIG** : la carte Leaflet/OpenStreetMap apporte une lecture géographique essentielle pour la supervision et la planification d’intervention.
- **IA non supervisée** : Isolation Forest permet la détection d’anomalies sans labels, avec un score de santé compréhensible et une synchronisation automatique des incidents.
- **Traçabilité et collaboration** : journal d’audit, rapports/export, messagerie interne et notifications.
- **Déploiement reproductible** : Docker Compose orchestre les services (postgres/api/simulation/frontend) et garantit un environnement stable pour la démonstration.

### Résultats et apports

Le projet démontre qu’une supervision plus intelligente peut être obtenue en combinant :

- une modélisation de données adaptée aux contraintes NOC (historisation des mesures) ;
- une API centralisant la logique métier et la sécurité ;
- une interface ergonomique orientée décision ;
- une IA intégrée et contrôlée (réduction faux positifs, séparation snapshot/calcul) ;
- une simulation temps réel pour valider le système.

### Compétences acquises

Sur le plan académique et professionnel, ce PFE a permis de développer :

- conception d’architecture web (frontend/backend, services, sécurité) ;
- maîtrise de React (composants, hooks, routing, charting, Leaflet) ;
- développement d’API Flask (blueprints, RBAC/JWT, intégration BD) ;
- modélisation BD PostgreSQL/PostGIS (contraintes, historisation) ;
- IA appliquée (prétraitement, Isolation Forest, scoring, intégration) ;
- conteneurisation et déploiement (Docker, healthchecks) ;
- conduite de projet Agile/Scrum et modélisation UML.

### Difficultés rencontrées (synthèse)

Les principales difficultés ont été :

- l’absence de données réelles labellisées (résolue par le choix non supervisé + simulation) ;
- la gestion des faux positifs (règles d’affinage + stabilité du snapshot) ;
- la cohérence multi-objets (antennes/mesures/incidents/audit) ;
- l’équilibre “temps réel” (polling) vs performance.

### Perspectives et améliorations futures

Pour une évolution vers un produit plus industriel, plusieurs axes sont envisageables :

- **Temps réel push** : WebSocket/SSE pour pousser incidents critiques au frontend.
- **Optimisation BD** : indexation avancée, partitionnement de la table mesures, stratégie d’archivage.
- **Observabilité** : ajout de métriques applicatives (Prometheus/Grafana), alerting.
- **IA avancée** :
  - calibrage dynamique des seuils selon zone/type d’antenne ;
  - modèles hybrides (saisonnalité, séries temporelles) ;
  - explicabilité plus riche (SHAP sur modèles supervisés si labels disponibles).
- **SIG avancé** : intégration complète GeoServer (couches WMS/WFS, styles, heatmaps, zones).
- **Sécurité** : durcissement (hash passwords robuste, rotation clés, audit complet, rate-limiting).
- **Gestion opérationnelle** : workflow incident plus complet (assignation, SLA, escalade).

### Mot de fin

En conclusion, ce PFE a permis de proposer une plateforme NOC cohérente et démontrable, centrée sur la supervision intelligente et la visualisation géographique. L’intégration de l’IA (Isolation Forest) et la simulation temps réel offrent une valeur ajoutée concrète, en rapprochant le projet des besoins opérationnels d’un centre technique. Les perspectives proposées ouvrent la voie à une industrialisation progressive et à l’intégration de nouvelles sources de données et de méthodes analytiques.

