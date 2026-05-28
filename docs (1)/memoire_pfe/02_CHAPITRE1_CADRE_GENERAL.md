# CHAPITRE 1 : CADRE GÉNÉRAL DU PROJET

## Introduction du chapitre

Ce premier chapitre situe le projet dans son environnement organisationnel et technique. Il présente l'organisme d'accueil, le contexte régional de Mahdia, l'état de l'art de la supervision télécom et la solution que nous avons conçue. L'objectif est de démontrer la pertinence industrielle du travail réalisé et les écarts comblés par rapport aux pratiques traditionnelles.

---

## 1.1 Présentation de Tunisie Télécom

**Tunisie Télécom** est l'opérateur historique des télécommunications en Tunisie. Acteur de référence sur le marché de la téléphonie fixe, de l'accès Internet et des services mobiles, l'entreprise assure la couverture nationale et investit continuellement dans la modernisation de ses infrastructures.

Ses missions couvrent notamment :

- le déploiement et la maintenance du réseau d'accès (cuivre, fibre, radio) ;
- l'exploitation des plateformes de services (voix, data, cloud) ;
- le support client et la gestion de la qualité de service ;
- la coordination des centres techniques régionaux.

Dans une logique de **décentralisation opérationnelle**, les centres techniques régionaux disposent d'une autonomie d'exécution tout en respectant les procédures nationales de supervision et d'escalade.

**Figure 1.1 : Organigramme simplifié de Tunisie Télécom**

```
Direction Générale
    ├── Directions métier (Réseau, IT, Commercial…)
    └── Centres techniques régionaux
            └── Centre de Mahdia (supervision locale)
```

*Source : Réalisation personnelle — modèle conceptuel.*

---

## 1.2 Présentation du centre de Mahdia

Le **centre technique de Mahdia** assure la supervision et la maintenance des infrastructures télécoms sur le **gouvernorat de Mahdia**. Le territoire présente une configuration mixte : zone côtière urbanisée (Mahdia, Ksour Essef), hinterland agricole et localités côtières secondaires.

Le parc radio supervisé dans le cadre du PFE compte **121 antennes** réparties en **neuf zones** administratives (Bekalta, Bou Merwan, Chebba, Chorbane, El Jem, Ksour Essef, Mahdia, Melloulèche, Sidi Alouane). Chaque antenne est géoréférencée (latitude, longitude) et associée à des mesures périodiques stockées en base.

**Figure 1.2 : Localisation du centre technique de Mahdia**

[Insérer capture : carte du gouvernorat avec points antennes]

*Source : Réalisation personnelle — export depuis la plateforme (module Carte réseau).*

**Analyse :** La figure 1.2 illustre la dispersion géographique des sites. Cette configuration justifie l'intégration d'un module SIG : un tableau seul ne permet pas de percevoir immédiatement les clusters d'anomalies côtiers versus l'arrière-pays.

---

## 1.3 Activités du centre

Les activités quotidiennes du centre incluent :

1. **Monitoring** des indicateurs réseau (disponibilité, alarmes équipements) ;
2. **Traitement des incidents** signalés par les systèmes ou les abonnés ;
3. **Planification des interventions** des équipes terrain ;
4. **Reporting** périodique vers la direction régionale ;
5. **Coordination** avec les partenaires et les prestataires de maintenance.

Avant le projet, une partie de ces activités reposait sur des outils hétérogènes et des traitements manuels (feuilles de calcul, appels téléphoniques, courriels), source de latence et de perte d'information.

---

## 1.4 Contexte du projet

Le projet s'inscrit dans un **Projet de Fin d'Études (PFE)** de Licence en Informatique, spécialité Réseaux et Télécommunications, réalisé par **Malek Maadi** et **Abir Said** sous la co-encadre académique et professionnelle.

Le cahier des charges exprimé par le centre visait à disposer d'un **prototype opérationnel** démontrable en soutenance : plateforme web, base de données réelle, IA explicable et déploiement conteneurisé. Le périmètre géographique a été volontairement limité au gouvernorat de Mahdia pour garantir une faisabilité en quelques mois tout en conservant un volume de données représentatif.

---

## 1.5 Étude de l'existant

### 1.5.1 Supervision traditionnelle

Les systèmes de supervision télécom classiques (OSS/BSS, NMS) agrègent des traps SNMP, des syslog et des sondes de performance. Ils offrent :

- des tableaux de bord par équipement ;
- des corrélations d'alarmes basiques ;
- des historiques de performance (PM).

Cependant, leur déploiement complet est coûteux et leur paramétrage lourd. Au niveau d'un centre régional, on observe souvent un **compromis** : outils nationaux pour les agrégats, et outils locaux (Excel, scripts) pour les spécificités.

### 1.5.2 Alarmes réseau

Le modèle d'alarme suit généralement : *événement → alarme → ticket → intervention*. Les seuils sont définis par type d'équipement. Les limitations identifiées :

- seuils identiques pour des contextes géographiques différents ;
- peu de prise en compte des corrélations entre métriques ;
- documentation d'intervention dissociée de la visualisation cartographique.

### 1.5.3 Outils NOC

Les NOC nationaux utilisent des solutions intégrées (ticketing, visiophonie, procédures). Notre étude de l'existant local a révélé l'absence d'un **outil unifié** combinant carte, IA et messagerie interne adapté au parc Mahdia.

---

## 1.6 Critique de l'existant

| Limite | Impact opérationnel | Réponse apportée |
|--------|---------------------|------------------|
| Absence de prédiction | Détection tardive | Isolation Forest + score de risque |
| Traitement manuel | Charge opérateur | Incidents automatiques + workflow |
| Temps de réaction élevé | QoS dégradée | Alertes temps réel + bannière critique |
| Vision non spatiale | Déplacements non optimisés | Carte Leaflet/OSM |
| Traçabilité faible | Audit difficile | Journal d'audit PostgreSQL |
| Communication dispersée | Erreurs de coordination | Messagerie interne intégrée |

---

## 1.7 Solution proposée

La solution développée est une **plateforme web NOC** nommée **GEO-TÉLÉCOM** dans le dépôt du projet, composée de :

- **Frontend React** (JavaScript) : dashboard, carte, incidents, administration ;
- **API REST Flask** : authentification JWT, métier, IA, exports ;
- **PostgreSQL/PostGIS** : persistance relationnelle et géospatiale ;
- **Simulateur** : génération continue de métriques (Mean-Reverting Random Walk) ;
- **IoT optionnel** : capteur DHT11 sur le site ISET Mahdia via Arduino.

La plateforme actualise les données par **polling silencieux** (8 à 30 secondes selon le module) sans rechargement de page.

---

## 1.8 Méthodologie adoptée

### 1.8.1 Approche Agile

L'approche Agile privilégie des livraisons incrémentales et l'adaptation au feedback de l'encadrant. Les user stories sont priorisées selon la valeur métier : l'authentification et la consultation des antennes précèdent la messagerie ou les rapports PDF.

### 1.8.2 Scrum

| Élément | Description |
|---------|-------------|
| Product Owner | Encadrant professionnel (centre Mahdia) |
| Scrum Master | Alternance entre les deux stagiaires |
| Équipe de développement | 2 développeurs (binôme PFE) |
| Durée de sprint | 3 à 4 semaines |
| Cérémonies | Daily court, revue de sprint, rétrospective |

### 1.8.3 UML

La modélisation UML a porté sur :

- **diagramme de cas d'utilisation** (acteurs : Administrateur, Ingénieur réseau, Technicien) ;
- **diagramme de classes** (Antenne, Mesure, Incident, Utilisateur) ;
- **diagramme de déploiement** (conteneurs Docker).

Les diagrammes détaillés figurent en annexe.

---

## Conclusion du chapitre 1

Ce chapitre a permis de situer le projet dans l'écosystème Tunisie Télécom et de justifier la création d'une plateforme intégrée pour le centre de Mahdia. L'analyse critique de l'existant démontre que les approches par seuils statiques ne suffisent plus face à la complexité des métriques corrélées. La solution proposée, articulée autour du web moderne, de PostGIS et de l'Isolation Forest, répond à ces lacunes de manière cohérente et démontrable.

Le chapitre suivant détaillera la phase de préparation : expression des besoins, modélisation et architecture cible.

---

*Fin du chapitre 1 — environ 12 pages en mise en forme.*
