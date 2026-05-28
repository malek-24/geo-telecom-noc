## Chapitre 1 — Présentation de l’organisme, contexte et cadrage du projet

### Introduction du chapitre

Un mémoire de PFE en informatique ne se limite pas à décrire une solution technique ; il doit également expliquer **où** et **pourquoi** la solution a été conçue. Ce chapitre présente l’organisme d’accueil (Tunisie Télécom), le centre technique concerné (Mahdia), puis le contexte qui a motivé la réalisation d’une plateforme NOC intelligente. L’objectif est de donner au lecteur une compréhension claire du terrain, des contraintes et des enjeux opérationnels qui ont guidé les choix techniques.

---

### 1.1 Présentation de Tunisie Télécom

#### 1.1.1 Historique et positionnement

Tunisie Télécom est l’un des principaux opérateurs de télécommunications en Tunisie. Son rôle historique s’est construit autour du déploiement et de l’exploitation d’infrastructures nationales : réseau fixe, réseau mobile, accès internet, transmission et services aux entreprises. À travers l’évolution du marché, l’opérateur a dû renforcer sa capacité d’innovation et d’industrialisation des systèmes d’information, notamment pour répondre aux exigences de qualité de service, de disponibilité et d’expérience utilisateur.

Dans le cadre de l’exploitation réseau, l’opérateur assure :

- le déploiement et l’entretien des équipements ;
- la supervision continue du réseau ;
- l’intervention terrain en cas de panne ;
- l’amélioration progressive des performances et de la couverture.

Cette mission implique un volume élevé d’événements et de métriques, ce qui souligne la nécessité de plateformes de supervision évoluées.

#### 1.1.2 Missions et activités

Les missions principales de Tunisie Télécom peuvent être synthétisées autour de trois axes :

- **Fourniture de services** : voix, données, internet, services professionnels et solutions entreprises.
- **Gestion de l’infrastructure** : extension, modernisation, et maintien en condition opérationnelle du réseau.
- **Qualité et support** : supervision, gestion des incidents, relation client et amélioration continue.

#### 1.1.3 Organisation générale

L’organisation d’un opérateur télécom inclut typiquement :

- une direction technique (déploiement, maintenance, transmission) ;
- une direction systèmes d’information (applications, données, sécurité) ;
- des centres régionaux (supervision, équipes terrain, support local).

**Figure 1.1 : Organigramme de Tunisie Télécom (simplifié)**  
[Insérer Capture]  
Source : Réalisation personnelle

**Analyse de la figure 1.1.**  
Cette figure illustre une structuration typique en pôles (technique, SI, exploitation). Dans le cadre du PFE, cette organisation a une conséquence directe : la plateforme NOC doit être conçue pour faciliter la collaboration entre profils différents (ingénieur réseau, technicien terrain, administrateur), d’où l’importance d’une gestion des rôles (RBAC) et d’un journal d’audit.

#### 1.1.4 Tableau descriptif

**Tableau 1.1 : Présentation synthétique de Tunisie Télécom**

| Élément | Description |
|---|---|
| Statut | Opérateur national de télécommunications |
| Domaines | Fixe, mobile, internet, services entreprise |
| Enjeux techniques | Couverture, disponibilité, performance, maintenance |
| Enjeux SI | Traçabilité, automatisation, cybersécurité, données |
| Besoin NOC | Centraliser la supervision + accélérer la détection d’incidents |

---

### 1.2 Présentation du Centre Technique de Mahdia

#### 1.2.1 Rôle du centre

Le Centre Technique de Mahdia joue un rôle opérationnel dans la **supervision régionale** et la **maintenance** des infrastructures télécoms. Il intervient notamment sur :

- le suivi des antennes de la zone ;
- la prise en charge des incidents ;
- la coordination avec les équipes terrain ;
- la remontée d’informations vers d’autres entités (si nécessaire).

#### 1.2.2 Supervision et maintenance : contraintes terrain

Plusieurs contraintes caractérisent un centre technique :

- **réactivité** : l’incident doit être détecté et qualifié rapidement ;
- **charge** : plusieurs événements simultanés peuvent survenir, surtout lors de conditions météo, pics de trafic ou pannes électriques ;
- **traçabilité** : toute action (résolution, modification) doit être traçable ;
- **hétérogénéité** : diversité des types d’antennes, zones, équipements et contextes.

**Figure 1.2 : Localisation du Centre Technique de Mahdia**  
[Insérer Capture]  
Source : Réalisation personnelle

**Analyse de la figure 1.2.**  
La localisation géographique du centre et de la zone de couverture justifie l’intégration d’un module SIG : la distance entre sites, l’accessibilité et la répartition spatiale influencent directement la planification des interventions et la priorisation.

**Tableau 1.2 : Fiche descriptive du Centre Technique de Mahdia**

| Élément | Description |
|---|---|
| Type | Centre technique régional |
| Activités | Supervision, maintenance, intervention terrain, suivi incidents |
| Données manipulées | Alarmes, métriques, listes d’antennes, historiques |
| Utilisateurs | Administrateur, ingénieur réseau, technicien terrain |
| Besoin majeur | Vision temps réel + cartographie + aide IA |

**Figure 1.3 : Photo / vue illustrative du centre ou environnement de supervision**  
[Insérer Capture]  
Source : Réalisation personnelle

**Analyse de la figure 1.3.**  
L’environnement de supervision nécessite une interface claire, lisible et rapide à interpréter. Dans un centre technique, l’opérateur doit prendre des décisions sous contrainte de temps ; une UI moderne (KPI, codes couleur, carte interactive) contribue à réduire le temps de compréhension et donc le temps de réaction.

---

### 1.3 Cadre du projet

#### 1.3.1 Contexte : croissance des réseaux et multiplication des pannes

La croissance du réseau se traduit par :

- augmentation du nombre de sites ;
- diversification des technologies radio et des configurations ;
- plus de métriques à collecter (performance, énergie, environnement) ;
- complexification de la corrélation des événements.

De ce fait, la gestion des pannes devient plus complexe. Un incident peut être causé par un événement unique (panne matérielle), mais aussi par une chaîne de causes (dégradation progressive d’une métrique menant à une panne).

#### 1.3.2 Étude de l’existant : supervision classique

Avant la plateforme proposée, la supervision s’appuie souvent sur :

- **logs** et consoles d’équipements ;
- alarmes remontées par des systèmes de monitoring ;
- tableaux et listes non géographiques ;
- opérations manuelles de corrélation.

Ces outils restent utiles, mais ils peuvent manquer d’intégration et de capacité à fournir une vision “système” centrée sur la décision.

#### 1.3.3 Analyse critique de l’existant

**Tableau 1.3 : Analyse critique de l’existant (avant projet)**

| Critère | Situation classique | Limites observées | Besoin PFE |
|---|---|---|---|
| Réactivité | Alerte après seuil | Réaction tardive | Détection proactive |
| Bruit | Beaucoup d’alarmes | Fatigue d’alerte | Scoring + filtrage |
| Contexte géo | Souvent absent | Corrélation difficile | Carte SIG + zones |
| Traçabilité | Partielle | Actions peu historisées | Audit structuré |
| Communication | Outils séparés | Coordination lente | Messagerie intégrée |
| Analyse | Seuils fixes | Peu d’adaptabilité | IA non supervisée |

#### 1.3.4 Solution proposée

La solution proposée est une **plateforme NOC intelligente** intégrée, offrant :

- une vision unifiée (dashboard) ;
- une cartographie interactive des antennes (Leaflet/OSM) ;
- une gestion structurée des incidents ;
- un moteur IA d’anomalies (Isolation Forest) ;
- une simulation temps réel (génération de métriques) ;
- des fonctions d’administration (utilisateurs/rôles) ;
- un audit et des rapports exportables.

**Figure 1.4 : Schéma du flux de supervision (avant vs après)**  
[Insérer Schéma]  
Source : Réalisation personnelle

**Analyse de la figure 1.4.**  
La différence majeure entre une supervision classique et la plateforme proposée réside dans la boucle d’analyse : les métriques ne servent pas uniquement à déclencher des seuils, mais alimentent un pipeline IA qui produit un score, lequel est ensuite restitué dans le dashboard et la carte. Cette boucle réduit le délai de détection et améliore la priorisation.

---

### 1.4 Méthodologie (Agile, Scrum, UML)

Le projet suit une démarche Agile, structurée en sprints. Chaque sprint produit un livrable fonctionnel et testable :

- **Sprint 1** : mise en place backend/BD/SIG/Docker.
- **Sprint 2** : développement du frontend React, dashboard, carte, pages et intégrations.
- **Sprint 3** : module IA (Isolation Forest), scoring et synchronisation incidents.
- **Sprint 4** : simulation temps réel, aspects IoT et raffinement temps réel.

UML est utilisé pour formaliser les besoins (cas d’utilisation), décrire les interactions (séquences) et structurer le système (classes, déploiement).

---

### Conclusion du chapitre 1

Ce chapitre a présenté Tunisie Télécom, le Centre Technique de Mahdia et le contexte opérationnel de la supervision d’un réseau télécom. L’étude critique de l’existant a mis en évidence des limites (absence de SIG intégré, supervision réactive, manque d’IA et de traçabilité), ce qui motive la conception d’une plateforme NOC intelligente. Le chapitre suivant détaille la capture des besoins, la modélisation UML et l’organisation Scrum adoptée pour structurer la réalisation du projet.

