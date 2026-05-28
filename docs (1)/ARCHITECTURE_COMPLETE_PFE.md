# Sprint 1 — Infrastructure SIG (stack actuelle)

L'objectif du Sprint 1 est la mise en place d'une infrastructure solide et modulaire via **Docker** : **PostgreSQL/PostGIS**, **GeoServer**, **API Flask** et **frontend React**. Ce socle supporte la supervision NOC et l'analyse IA.

> **Note :** GeoNetwork (catalogue) et Grafana (observabilité) ont été retirés du `docker-compose.yml`. La supervision opérationnelle est assurée par le dashboard React et l'API.

## Objectifs livrés

1. **Docker Compose** : réseau `sig_net`, volumes persistants.
2. **PostgreSQL/PostGIS** : schéma `antennes`, `mesures`, vues `antennes_geo`, `antennes_statut`.
3. **GeoServer** : publication WMS/WFS (port hôte **8080**).
4. **API Flask** + **simulation** des mesures.
5. **Frontend React** servi par Nginx (port **3000**).

## Interactions

1. L'utilisateur consulte le **dashboard React** (KPI, incidents, carte).
2. La carte peut superposer une couche **WMS GeoServer** ou des marqueurs issus de l'API.
3. **GeoServer** lit PostGIS via un datastore configuré manuellement ou par script.

## Résultat

Infrastructure géospatiale opérationnelle : données en base, API JSON, visualisation cartographique et couches SIG via GeoServer.
