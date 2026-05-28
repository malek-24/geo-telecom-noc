# INTRODUCTION GÉNÉRALE

## Contexte des télécommunications en Tunisie

La Tunisie a connu, au cours des deux dernières décennies, une transformation profonde de son paysage numérique. La généralisation de l'accès mobile, l'essor de la 4G puis les expérimentations autour de la 5G ont placé les opérateurs historiques, dont **Tunisie Télécom (TT)**, au cœur d'enjeux techniques et organisationnels majeurs. La qualité perçue par l'abonné dépend directement de la disponibilité des infrastructures radio : antennes relais, équipements de transmission, alimentation, refroidissement et capacité de traitement des équipements actifs.

Dans ce contexte, la **supervision réseau** n'est plus une fonction accessoire : elle constitue un pilier de la continuité de service. Les équipes techniques doivent détecter les dérives de performance, localiser les sites affectés et coordonner les interventions terrain dans des délais compatibles avec les engagements de qualité de service (QoS). Les centres d'exploitation, ou **NOC** (*Network Operations Center*), centralisent cette activité en agrégeant alarmes, tickets et indicateurs de performance.

## Importance des réseaux mobiles et du rôle des NOC

Un réseau mobile repose sur un maillage de **sites radio** couvrant un territoire. Chaque site agrège des métriques techniques : température des baies, charge processeur (CPU), force du signal reçu (RSSI), latence de transmission et taux de disponibilité. Ces grandeurs, lorsqu'elles sont surveillées de manière continue, permettent d'anticiper les pannes ou les dégradations avant qu'elles n'impactent massivement les utilisateurs.

Le NOC assure plusieurs missions fondamentales :

- **Surveillance** : observation en temps quasi réel de l'état du parc ;
- **Corrélation** : regroupement des événements pour éviter la saturation par des alarmes redondantes ;
- **Escalade** : déclenchement de procédures d'intervention selon la criticité ;
- **Traçabilité** : conservation d'un historique pour l'analyse post-incident et l'amélioration continue.

À l'échelle régionale, le **centre technique de Mahdia** intervient sur un parc d'environ **121 antennes** réparties en **neuf zones** géographiques du gouvernorat. La dispersion spatiale des sites renforce l'intérêt d'outils cartographiques intégrés aux systèmes de supervision.

## Limites des méthodes traditionnelles

Historiquement, la supervision s'appuie sur des seuils statiques : si la température dépasse X degrés ou si la disponibilité descend sous Y pour cent, une alarme est émise. Cette approche présente des limites bien documentées :

1. **Rigidité** : les seuils ne s'adaptent pas aux profils saisonniers ou géographiques ;
2. **Faux positifs** : multiplication des alertes non actionnables, conduisant à une « fatigue d'alarme » ;
3. **Absence de corrélation multivariée** : une anomalie peut résulter d'une combinaison température + CPU + signal, invisible à des règles univariées ;
4. **Traitement manuel** : l'opérateur doit interpréter, prioriser et documenter, ce qui allonge le temps de réaction ;
5. **Vision fragmentée** : données techniques, géographiques et organisationnelles dispersées dans plusieurs outils.

Ces limites motivent l'introduction de l'**intelligence artificielle** pour la détection d'anomalies et des **SIG** pour la spatialisation des informations.

## Intelligence artificielle dans les télécommunications

L'apprentissage automatique (*machine learning*) offre des méthodes de détection d'anomalies **non supervisées**, adaptées lorsque les données « normales » sont abondantes mais les cas d'anomalie rares ou imprévisibles. Parmi les algorithmes pertinents figure **Isolation Forest** : il isole les observations atypiques dans un espace de features multidimensionnel sans nécessiter d'étiquetage exhaustif des pannes passées.

Dans notre projet, le modèle analyse cinq métriques réseau — température, CPU, signal, latence, disponibilité — enrichies éventuellement d'un contexte géographique (voisinage spatial). Il produit un **score de risque** et une **classification** en trois états métier : *normal*, *alerte* et *critique*, déclenchant la création d'incidents lorsque nécessaire.

## SIG dans les réseaux télécoms

Un **système d'information géographique (SIG)** associe des données attributaires à des coordonnées spatiales. Pour la supervision radio, la cartographie permet de :

- visualiser la couverture et la densité des sites ;
- identifier les zones géographiquement concentrées en anomalies ;
- faciliter la planification des déplacements des techniciens.

Notre plateforme s'appuie sur **PostgreSQL/PostGIS** pour le stockage géoréférencé et sur **Leaflet** avec fond **OpenStreetMap** pour l'affichage web, sans dépendance à un serveur cartographique propriétaire supplémentaire.

## Problématique

Comment concevoir et développer une plateforme web intégrée permettant au centre NOC de Mahdia de **superviser**, **analyser** et **réagir** face aux anomalies réseau sur un parc d'antennes distribué, en combinant visualisation cartographique, détection automatique par IA et traçabilité des opérations ?

Cette problématique se décline en sous-questions :

- Quelle architecture logicielle garantit maintenabilité, sécurité et évolutivité ?
- Comment modéliser et persister les entités métier (antennes, mesures, incidents, utilisateurs) ?
- Quel algorithme d'IA choisir pour limiter les faux positifs tout en détectant les dérives réelles ?
- Comment offrir une expérience utilisateur adaptée aux rôles NOC (administrateur, ingénieur, technicien) ?

## Objectifs du projet

### Objectif général

Concevoir et réaliser une **plateforme NOC intelligente** dédiée à la supervision des antennes télécoms du gouvernorat de Mahdia, intégrant IA et SIG.

### Objectifs spécifiques

| N° | Objectif | Indicateur de réussite |
|----|----------|------------------------|
| O1 | Centraliser la supervision des antennes | Consultation unique via dashboard et carte |
| O2 | Automatiser la détection d'anomalies | Pipeline Isolation Forest opérationnel |
| O3 | Gérer le cycle de vie des incidents | CRUD incidents + résolution + historique |
| O4 | Cartographier le parc radio | Affichage Leaflet/OSM avec statuts colorés |
| O5 | Sécuriser les accès | Authentification JWT et rôles |
| O6 | Tracer les opérations sensibles | Journal d'audit persistant |
| O7 | Faciliter la communication interne | Messagerie publique et privée |
| O8 | Produire des rapports | Exports PDF, Excel et CSV |
| O9 | Conteneuriser le déploiement | Stack Docker Compose reproductible |

## Méthodologie Scrum

Le projet a été mené selon une approche **Agile Scrum** sur quatre sprints thématiques :

1. **Sprint 1** — Backend, base de données, Docker ;
2. **Sprint 2** — Interface React et modules métier ;
3. **Sprint 3** — Intelligence artificielle et intégration ;
4. **Sprint 4** — Simulation temps réel et IoT (capteur DHT11).

Chaque sprint comporte planification, développement, tests et revue, avec un backlog produit priorisé en collaboration avec l'encadrement professionnel.

## Organisation du mémoire

Le présent document s'organise en six chapitres :

- Le **chapitre 1** présente le cadre institutionnel et l'étude de l'existant ;
- Le **chapitre 2** détaille l'analyse des besoins et la modélisation UML ;
- Le **chapitre 3** traite du sprint backend et de l'infrastructure ;
- Le **chapitre 4**, le plus volumineux, documente le frontend et les interfaces utilisateur ;
- Le **chapitre 5** approfondit le module d'intelligence artificielle ;
- Le **chapitre 6** décrit la simulation et l'IoT.

La **conclusion générale** synthétise les apports et les perspectives. Les **annexes** regroupent schémas, extraits de code et documentation API.

---

**Figure 0.1 : Architecture globale de la plateforme NOC**

```
[Utilisateurs NOC] → [Navigateur React :3000]
        ↓ HTTPS / REST + JWT
[API Flask + Gunicorn :7000] → [PostgreSQL/PostGIS :6000]
        ↑                           ↑
[Simulateur MRRW]              [PostGIS geom]
[Arduino DHT11 → /iot/mesure]
```

*Source : Réalisation personnelle — d'après docker-compose.yml du projet.*

---

*Fin de l'introduction générale — environ 8 à 10 pages en mise en forme académique.*
