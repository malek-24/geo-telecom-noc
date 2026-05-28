# CONCLUSION GÉNÉRALE

## Synthèse du projet

Ce mémoire a présenté la conception et le développement d'une plateforme intelligente de supervision des réseaux télécoms, réalisée au centre technique de **Tunisie Télécom — Mahdia**. Le livrable combine une interface web React, une API Flask, une base PostgreSQL/PostGIS, un moteur de détection d'anomalies par **Isolation Forest** et une infrastructure Docker Compose.

Le système supervise environ **121 antennes** réparties en neuf zones, avec gestion des incidents, cartographie Leaflet/OpenStreetMap, messagerie interne, journal d'audit et exports de rapports.

## Résultats obtenus

| Objectif | Résultat |
|----------|----------|
| Centralisation | Plateforme unique opérationnelle |
| IA | Pipeline IF intégré, statuts normal/alerte/critique |
| SIG | Carte interactive + PostGIS |
| Sécurité | JWT + rôles + audit |
| Déploiement | `docker compose up` reproductible |

## Compétences acquises

- Conception d'API REST et modélisation relationnelle/géospatiale ;
- Développement React et visualisation de données ;
- Machine learning appliqué (Scikit-learn) ;
- Conteneurisation et orchestration légère ;
- Travail en binôme avec méthode Scrum.

## Difficultés rencontrées

- Alignement des fuseaux horaires (Africa/Tunis) entre backend et frontend ;
- Migration progressive du schéma messagerie (`messages_chat`) ;
- Équilibre entre réactivité UI (polling) et charge serveur ;
- Calibration du modèle IF pour limiter les faux positifs en démo.

## Apport du projet

Pour le centre de Mahdia, la plateforme constitue un **prototype crédible** de NOC régional modernisé, démontrable en soutenance et extensible. Pour les auteurs, il matérialise le lien entre formation académique et besoins industriels télécoms.

## Perspectives d'amélioration

1. Migration **TypeScript** et tests automatisés (Jest, Pytest) ;
2. WebSockets pour push temps réel au lieu du polling ;
3. Tableau de bord mobile pour techniciens terrain ;
4. Modèles prédictifs (séries temporelles) ;
5. Intégration alarmes SNMP/NETCONF des équipements réels ;
6. Authentification LDAP/Active Directory entreprise ;
7. Haute disponibilité PostgreSQL et monitoring Prometheus.

---

# ANNEXES

## Annexe A — Diagramme de déploiement UML

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   frontend   │     │     api      │     │  postgres    │
│   :3000      │────►│   :7000      │────►│   :6000      │
└──────────────┘     └──────┬───────┘     └──────────────┘
                            │
                     ┌──────▼───────┐
                     │ simulation   │
                     └──────────────┘
```

## Annexe B — Schéma base de données

Voir fichier projet `database/init.sql` — tables `antennes`, `mesures`, `incidents`, `users`, `audit_logs`, `messages_chat`.

## Annexe C — Extrait code — prédiction IA

```python
# api/ia/prediction.py (extrait conceptuel)
# Mesure → train_and_predict → scoring → statut → incident
```

## Annexe D — Catalogue API REST

Référence complète : routes dans `api/routes/` (auth, antennes, incidents, ia, chat, audit, export, reports, iot).

## Annexe E — Captures d'écran supplémentaires

- Figure E.1 : Page login  
- Figure E.2 : Export CSV  
- Figure E.3 : Logs Docker  

---

# BIBLIOGRAPHIE

1. Hastie T., Tibshirani R., Friedman J. (2009). *The Elements of Statistical Learning*. Springer.  
2. Liu F. T., Ting K. M., Zhou Z. H. (2008). *Isolation Forest*. ICDM.  
3. Pedregosa F. et al. (2011). *Scikit-learn: Machine Learning in Python*. JMLR.  
4. Fielding R. T. (2000). *Architectural Styles and the Design of Network-based Software Architectures*. Dissertation REST.  
5. OpenStreetMap contributors. *OpenStreetMap*. https://www.openstreetmap.org  
6. PostgreSQL Global Development Group. *PostgreSQL Documentation*. https://www.postgresql.org/docs/  
7. PostGIS Project. *PostGIS Documentation*. https://postgis.net/documentation/  
8. Facebook Inc. *React Documentation*. https://react.dev  
9. Pallets Projects. *Flask Documentation*. https://flask.palletsprojects.com  
10. ITU-T (2017). *E.800 series — Definitions of terms related to quality of service*.  
11. Tanenbaum A., Wetherall D. (2011). *Computer Networks*. Pearson.  
12. Sommerville I. (2015). *Software Engineering*. Pearson.  
13. Schwaber K., Sutherland J. (2020). *The Scrum Guide*.  
14. OGC. *OpenGIS Implementation Standard for Geographic information*.  
15. Docker Inc. *Docker Documentation*. https://docs.docker.com  

---

# GLOSSAIRE

| Terme | Définition |
|-------|------------|
| Antenne (site radio) | Équipement de couverture mobile géoréférencé |
| Incident | Ticket décrivant un dysfonctionnement ou une anomalie |
| Isolation Forest | Algorithme de détection d'anomalies non supervisé |
| JWT | Token signé pour authentification stateless |
| Mesure | Enregistrement temporel des métriques d'une antenne |
| NOC | Centre d'exploitation et de supervision réseau |
| RSSI | Indicateur de puissance du signal reçu |
| Sprint | Itération Scrum de livraison |

---

*Fin du mémoire — Compiler l'ensemble des fichiers pour atteindre 80–100 pages en PDF (Times 12, interligne 1,5, marges 2,5 cm).*
