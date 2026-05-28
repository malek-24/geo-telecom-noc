## Annexes

### Annexe A — Backlog complet (exemple extensible)

Cette annexe propose une forme de backlog complet. Elle peut être enrichie avec vos tickets, estimations, et burndown.

**Tableau A.1 : Backlog produit (version synthétique)**

| Module | Fonction | Priorité | Statut |
|---|---|---|---|
| Auth | Login + JWT + RBAC | Haute | Réalisé |
| Dashboard | KPI + graph + incidents | Haute | Réalisé |
| Carte SIG | Leaflet + OSM + markers | Haute | Réalisé |
| Antennes | Liste + historique | Haute | Réalisé |
| Incidents | gestion + résolution | Haute | Réalisé |
| IA | Isolation Forest + scoring | Haute | Réalisé |
| Simulation | métriques + scénarios | Haute | Réalisé |
| Admin | utilisateurs + rôles | Moyenne | Réalisé |
| Audit | journal actions | Moyenne | Réalisé |
| Rapports | stats + export CSV | Moyenne | Réalisé |
| Chat | public + privé + notif | Moyenne | Réalisé |

---

### Annexe B — Diagramme de déploiement (Docker)

**Figure B.1 : Diagramme de déploiement (conteneurs Docker)**  
[Insérer Diagramme]  
Source : Réalisation personnelle

```mermaid
flowchart TB
  subgraph Host[Machine hôte]
    subgraph Net[sig_net (bridge)]
      PG[(postgres\npostgis/postgis:15-3.4\n6000:5432)]
      API[api\nFlask+Gunicorn\n7000:5000]
      SIM[simulation\nmetrics generator]
      FE[frontend\nNginx + React\n3000:80]
    end
    VOL[(Volume postgres_data)]
  end

  VOL --- PG
  API --> PG
  SIM --> PG
  SIM --> API
  FE --> API
```

---

### Annexe C — Glossaire (extraits)

- **Incident** : événement opérationnel affectant un service/site, nécessitant suivi et résolution.
- **Alerte** : statut intermédiaire indiquant une dégradation modérée.
- **Critique** : statut indiquant une anomalie forte, prioritaire.
- **Score santé** : indicateur IA (0–100) de l’état d’un site.

---

### Annexe D — Emplacements des captures d’écran

Pour respecter les exigences (35+ figures), insérer des captures réelles dans :

- Login, Dashboard, Carte (vue globale + popup + filtres)
- Pages Antennes, Historique, Incidents, Admin, Audit, Reports, Export CSV
- Chat (public, privé, notifications)
- Docker (services démarrés), API (healthcheck), PostgreSQL (tables)
- IA (test-ia, predict snapshot, info modèle)

Format attendu pour chaque figure :

**Figure X.Y : Nom de la capture**  
[Insérer Capture]  
Source : Réalisation personnelle

Puis une analyse :

- rôle de l’interface ;
- fonctionnalités affichées ;
- importance dans le système ;
- interaction utilisateur ;
- intégration avec l’API ;
- intérêt pour la supervision télécom.

---

### Annexe E — Spécification API REST (catalogue détaillé)

Cette annexe consolide la surface API de la plateforme. Elle sert de référence pour :

- la cohérence Frontend ↔ Backend ;
- la sécurité (authentifié / rôle requis) ;
- la validation (tests fonctionnels).

> Remarque : les endpoints exacts peuvent varier selon les fichiers routes ; l’objectif ici est de fournir un catalogue complet “style mémoire”.

**Tableau E.1 : Catalogue des endpoints (extrait long)**

| Domaine | Méthode | Endpoint | Auth | Rôle | Description | Réponse attendue |
|---|---:|---|---:|---|---|---|
| Santé | GET | `/health` | Non | — | healthcheck Docker | `{status:"ok"}` |
| Auth | POST | `/auth/login` | Non | — | login, retourne JWT | token + user |
| Antennes | GET | `/antennes` | Oui | tous | liste + métriques + score | `[ {...} ]` |
| Antennes | GET | `/antennes/:id` | Oui | tous | détails antenne | `{...}` |
| Antennes | GET | `/antenne/:id/history` | Oui | tous | historique mesures | `[ {time,...} ]` |
| Dashboard | GET | `/dashboard/summary` | Oui | tous | KPI (normal/alertes/critique, dispo, score) | `{...}` |
| Dashboard | GET | `/dashboard/history` | Oui | tous | courbes 12h (dispo) | `[ {...} ]` |
| Incidents | GET | `/incidents` | Oui | tous | liste incidents | `[ {...} ]` |
| Incidents | POST | `/incidents/:id/resolve` | Oui | technicien/ingénieur/admin | résolution manuelle | `{success:true}` |
| IA | GET | `/predict` | Oui | tous | snapshot IA depuis BD | `[ {id,statut,risk_score} ]` |
| IA | GET | `/internal/predict` | Non | — | calcul IA (simulation/IoT) | `[ {...} ]` |
| IA | POST | `/ia/retrain` | Oui | admin/ingénieur | réentraîner modèle | `{success:true}` |
| IA | POST | `/ia/reset` | Oui | admin | reset complet | `{success:true}` |
| IA | GET | `/ia/model/info` | Oui | tous | infos modèle (paramètres) | `{...}` |
| IA (démo) | POST | `/api/test-ia` | Oui | tous | injection anomalie (jury) | `{success:true,...}` |
| Chat public | GET | `/chat/messages` | Oui | tous | historique messages | `[ {...} ]` |
| Chat public | POST | `/chat/messages` | Oui | tous | envoyer message | `{id,...}` |
| Chat public | GET | `/chat/messages/new?since_id=...` | Oui | tous | nouveaux messages | `[ {...} ]` |
| Chat privé | GET | `/chat/private/:user_id` | Oui | tous | historique privé | `[ {...} ]` |
| Chat privé | POST | `/chat/private/:user_id` | Oui | tous | envoyer privé | `{id,...}` |
| Chat | GET | `/chat/users` | Oui | tous | liste utilisateurs | `[ {id,username,role} ]` |
| Chat | GET | `/chat/unread/summary` | Oui | tous | total non lus + par expéditeur | `{total,...}` |
| Audit | GET | `/audit/logs` | Oui | admin/ingénieur | consulter audit | `[ {...} ]` |
| Export | GET | `/export/csv?...` | Oui | tous | export CSV | fichier |

**Analyse (annexe E).**  
Le catalogue met en évidence une architecture “centrée API”. Les endpoints critiques sont sécurisés, tandis que les endpoints internes (simulation) sont isolés. Cette séparation réduit les risques d’appel involontaire depuis l’UI et garantit un comportement stable côté NOC.

---

### Annexe F — Dictionnaire de données (BD PostgreSQL/PostGIS)

Cette annexe décrit les principales tables et leurs champs, dans un format “fiche” utile pour la documentation et la maintenance.

**Tableau F.1 : Table `antennes` (exemple)**

| Champ | Type | Contraintes | Description |
|---|---|---|---|
| `id` | int | PK | identifiant unique |
| `nom` | text | unique (souhaité) | nom opérationnel (TT-xxx) |
| `zone` | text | — | zone géographique |
| `type` | text | — | type antenne/site |
| `latitude` | float | not null | coordonnée |
| `longitude` | float | not null | coordonnée |
| `statut` | text | enum logique | normal/alerte/critique/maintenance |

**Tableau F.2 : Table `mesures` (exemple)**

| Champ | Type | Contraintes | Description |
|---|---|---|---|
| `id` | int | PK | identifiant mesure |
| `antenne_id` | int | FK | référence antenne |
| `temperature` | float | — | °C |
| `cpu` | float | — | % |
| `signal` | float | — | dBm |
| `latence` | float | — | ms |
| `disponibilite` | float | — | % |
| `statut` | text | — | statut dérivé IA |
| `risk_score` | float | — | score santé 0–100 |
| `date_mesure` | timestamp | index | horodatage |

**Tableau F.3 : Table `incidents` (exemple)**

| Champ | Type | Contraintes | Description |
|---|---|---|---|
| `id` | int | PK | identifiant |
| `antenne_id` | int | FK | site concerné |
| `titre` | text | — | diagnostic synthétique |
| `description` | text | — | détails |
| `criticite` | text | — | warning/critical |
| `statut` | text | — | en_cours / resolu |
| `source_detection` | text | — | IA / manuel |
| `metriques` | jsonb | — | snapshot métriques |
| `date_creation` | timestamp | — | début |
| `date_resolution` | timestamp | — | fin |

---

### Annexe G — Matrice de sécurité (RBAC) : rôles × actions

**Tableau G.1 : Matrice RBAC (exemple)**

| Action | Technicien | Ingénieur | Admin |
|---|---:|---:|---:|
| Consulter dashboard/carte | Oui | Oui | Oui |
| Consulter antennes/historique | Oui | Oui | Oui |
| Consulter incidents | Oui | Oui | Oui |
| Résoudre incident | Oui | Oui | Oui |
| Consulter audit | Non | Oui | Oui |
| Gérer utilisateurs | Non | Non | Oui |
| Réentraîner modèle IA | Non | Oui | Oui |
| Reset modèle IA | Non | Non | Oui |

---

### Annexe H — Plan de tests complet (scénarios de soutenance)

Cette annexe propose une série de scénarios “jury” permettant de démontrer la plateforme de façon structurée.

**Tableau H.1 : Scénarios de démonstration (détaillé)**

| Scénario | Étapes | Critères de réussite | Pages concernées |
|---|---|---|---|
| D1 — Démarrage stack | `docker compose up` | services healthy | Docker + health |
| D2 — Login | se connecter admin | accès + rôle visible | Login, Dashboard |
| D3 — État normal | vérifier KPI | 0 incident actif | Dashboard |
| D4 — Injection surchauffe | appeler `test-ia` | incident critical créé | Dashboard, Incidents, Carte |
| D5 — Localisation | filtre “critique” | site visible sur carte | Carte |
| D6 — Diagnostic | ouvrir popup | métriques anormales visibles | Carte |
| D7 — Résolution | résoudre incident | statut normal + audit | Incidents, Audit |
| D8 — Chat | envoyer msg public | réception + non lus | Chat |
| D9 — Rapport | export CSV | fichier téléchargé | Reports |


