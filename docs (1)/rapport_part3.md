# CHAPITRE 5 : SPRINT 3 — INTELLIGENCE ARTIFICIELLE

## Introduction

Le Sprint 3 constitue le cœur scientifique du projet. L'objectif est d'intégrer un moteur d'intelligence artificielle capable de détecter automatiquement les anomalies réseau, de calculer un score de risque pour chaque antenne, et de déclencher la création automatique d'incidents. L'algorithme retenu est **Isolation Forest**, un modèle non supervisé particulièrement adapté à la détection d'anomalies dans des flux de données multivariées.

## 5.1 Backlog du Sprint 3

| ID | Tâche | Priorité |
|---|---|---|
| T20 | Implémentation du modèle Isolation Forest (`ia/model.py`) | Haute |
| T21 | Pipeline de prédiction complet (`ia/prediction.py`) | Haute |
| T22 | Calcul du score de risque normalisé (`ia/scoring.py`) | Haute |
| T23 | Moteur de diagnostic automatique (`ia/diagnostics.py`) | Haute |
| T24 | Synchronisation automatique des incidents IA | Haute |
| T25 | Endpoint `/internal/predict` (déclenché par le simulateur) | Haute |
| T26 | Génération de rapports PDF avec analyse IA (ReportLab) | Moyenne |
| T27 | Export Excel des données réseau (openpyxl) | Moyenne |

## 5.2 Analyse des données

### Les 8 métriques analysées

Le modèle Isolation Forest analyse simultanément **8 métriques réseau** pour chaque antenne :

| Métrique | Unité | Plage normale | Seuil d'alerte |
|---|---|---|---|
| `temperature` | °C | 25 – 45 | > 60 |
| `cpu` | % | 10 – 60 | > 80 |
| `ram` | % | 20 – 65 | > 85 |
| `debit` (traffic) | Mbps | 100 – 1000 (4G), 500 – 1500 (5G) | < 10% nominal |
| `latence` | ms | 5 – 30 | > 100 |
| `packet_loss` | % | 0 – 1 | > 5 |
| `disponibilite` | % | 97 – 100 | < 90 |
| `jitter` | ms | 1 – 15 | > 50 |

### Caractéristiques du jeu de données

- **Volume** : 120 antennes × 1 mesure par cycle = 120 observations par inférence
- **Fréquence** : toutes les 10 minutes (cycle de simulation)
- **Type** : données continues multivariées, sans étiquettes (apprentissage non supervisé)
- **Imputation** : les valeurs manquantes sont remplacées par la médiane de la colonne

## 5.3 Conception du modèle IA

### Isolation Forest — Principe

L'Isolation Forest est un algorithme de détection d'anomalies non supervisé. Son principe repose sur la construction de forêts d'arbres de décision aléatoires :

1. **Isolation** : l'algorithme isole chaque observation en sélectionnant aléatoirement une feature, puis une valeur de coupure entre son min et son max
2. **Profondeur d'isolation** : les anomalies nécessitent moins de coupures pour être isolées (arbres plus courts)
3. **Score d'anomalie** : la `decision_function` retourne un score négatif pour les anomalies (plus négatif = plus anormal)

**Avantages pour notre cas d'usage** :
- Fonctionne sans données étiquetées (pas de pannes historiques labellisées nécessaires)
- Efficace sur des données multivariées (8 métriques simultanées)
- Complexité O(n·log n), adapté au traitement temps réel de 120 antennes
- Robuste aux valeurs aberrantes dans les données d'entraînement

### Architecture du module IA

```
ia/
├── model.py       ← IsolationForest.fit_predict() + decision_function()
├── prediction.py  ← Orchestrateur : DB → IA → statut → incidents
├── scoring.py     ← Normalisation score 0-100 + seuils statut
└── diagnostics.py ← Identification de la métrique responsable
```

### Pipeline IA complet

```
PostgreSQL (antennes_statut)
    │
    ▼ pd.read_sql()
DataFrame 120 antennes × 8 features
    │
    ▼ train_and_predict()
IsolationForest(contamination=0.08, random_state=42)
    ├── anomaly_output : [-1, 1] par antenne
    └── risk_level : decision_function scores
    │
    ▼ calculate_risk_score()
risk_score normalisé [0, 100]
    │
    ▼ determine_statut_final()
    ├── ≥ 70 → 'critique'
    ├── ≥ 40 → 'alerte'
    └── < 40 → 'normal'
    │
    ▼ diagnostiquer_incident()
Identification de la métrique déviante (température, CPU, latence, packet_loss)
    │
    ▼ UPDATE mesures + antennes (PostgreSQL)
    │
    ▼ synchroniser_incidents_isolation_forest()
    ├── alerte/critique + pas d'incident actif → INSERT incidents
    ├── critique + incident actif → UPDATE criticite='critical'
    └── normal + incident actif → UPDATE statut='resolu'
```

## 5.4 Réalisation

### Module `model.py` — Entraînement et prédiction

```python
ML_FEATURES = [
    "temperature", "cpu", "ram", "debit",
    "latence", "packet_loss", "disponibilite", "jitter"
]

def train_and_predict(df, contamination_rate=0.08):
    # Imputation des valeurs manquantes par la médiane
    for col in ML_FEATURES:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(df[col].median())
    
    # Entraînement et prédiction en une seule passe
    model = IsolationForest(contamination=contamination_rate, random_state=42)
    anomaly_output = model.fit_predict(df[ML_FEATURES])   # -1 = anomalie, 1 = normal
    risk_level = model.decision_function(df[ML_FEATURES]) # scores bruts
    
    return anomaly_output, risk_level
```

**Paramètre `contamination=0.08`** : le modèle s'attend à ce que 8% des antennes soient anormales à tout moment, ce qui correspond à environ 9-10 antennes sur 120.

### Module `scoring.py` — Normalisation du score

```python
def calculate_risk_score(risk_level, min_score, max_score):
    """
    Normalise la decision_function d'Isolation Forest
    en un score de risque [0, 100] compréhensible.
    Score élevé = risque élevé.
    """
    if max_score != min_score:
        return 100 * (1 - (risk_level - min_score) / (max_score - min_score))
    return 0

def determine_statut_final(risk_score):
    if risk_score >= 70: return 'critique'
    elif risk_score >= 40: return 'alerte'
    else: return 'normal'
```

### Module `diagnostics.py` — Identification des causes

```python
def diagnostiquer_incident(row):
    """
    Identifie quelle métrique est responsable de l'anomalie
    en calculant l'écart par rapport aux seuils empiriques.
    """
    deviations = {
        "Température":       max(0, float(row.get("temperature") or 0) - 45),
        "CPU":               max(0, float(row.get("cpu") or 0) - 50),
        "Latence":           max(0, float(row.get("latence") or 0) - 30),
        "Perte de Paquets":  max(0, float(row.get("packet_loss") or 0) - 1) * 10
    }
    worst_metric = max(deviations, key=deviations.get)
    
    titre = f"Anomalie IA détectée : {worst_metric}"
    desc  = f"Le modèle Isolation Forest a identifié une déviation statistique majeure sur {worst_metric}."
    return titre, desc
```

### Module `prediction.py` — Synchronisation des incidents

La fonction `synchroniser_incidents_isolation_forest()` implémente la logique métier de gestion automatique du cycle de vie des incidents :

```python
for _, row in df.iterrows():
    statut = row["new_statut"]
    
    # Vérifie si un incident actif existe déjà
    cur.execute("SELECT id FROM incidents WHERE antenne_id = %s AND statut != 'resolu'", (ant_id,))
    active_incident = cur.fetchone()

    if statut in ['alerte', 'critique'] and not active_incident:
        # Créer un nouvel incident avec les métriques contextuelles
        cur.execute("""
            INSERT INTO incidents (antenne_id, titre, criticite, source_detection, metriques)
            VALUES (%s, %s, %s, 'Isolation Forest', %s::jsonb)
        """, (ant_id, titre, criticite, json.dumps(metrics)))
    
    elif statut == 'normal' and active_incident:
        # Résoudre automatiquement l'incident
        cur.execute("UPDATE incidents SET statut='resolu', date_resolution=NOW() WHERE id=%s",
                    (active_incident[0],))
```

### Génération de rapports (reports_routes.py)

Le module de rapports utilise **ReportLab** pour générer des PDF et **openpyxl** pour les exports Excel. Les rapports IA incluent :
- Résumé des anomalies détectées (nombre, criticité, zones affectées)
- Tableau des antennes avec leurs scores de risque
- Graphiques de distribution des métriques
- Recommandations automatiques basées sur les diagnostics

## Conclusion

Le Sprint 3 a intégré un moteur d'intelligence artificielle complet et autonome. L'Isolation Forest analyse les 8 métriques réseau de toutes les antennes à chaque cycle, détermine automatiquement leur statut, et gère le cycle de vie des incidents sans intervention humaine. Cette approche non supervisée est particulièrement adaptée au contexte réel où les pannes étiquetées sont rares.

---

# CHAPITRE 6 : SPRINT 4 — IOT & SIMULATION

## Introduction

Le Sprint 4 clôture le développement en apportant la dimension temps réel. Sans équipements physiques disponibles, un moteur de simulation génère des données réseau réalistes, reproduisant le comportement naturel d'un réseau télécom : évolution progressive des métriques, dégradations graduelles, et anomalies critiques sporadiques.

## 6.1 Backlog du Sprint 4

| ID | Tâche | Priorité |
|---|---|---|
| T28 | Moteur de simulation avec dérive progressive (`generate_mesures.py`) | Haute |
| T29 | Planification automatique avec `schedule` (toutes les 10 minutes) | Haute |
| T30 | Seed initial des 120 antennes (`generate_antennes.py`) | Haute |
| T31 | Intégration du déclencheur IA après chaque cycle | Haute |
| T32 | Retry automatique de connexion PostgreSQL (20 tentatives) | Haute |
| T33 | Attente de disponibilité de l'API avant premier cycle | Moyenne |
| T34 | Bannière temps réel `CriticalAlertBanner.js` (poll 15s) | Haute |
| T35 | Chat interne NOC `ChatWidget.js` | Moyenne |
| T36 | Historique des métriques par antenne `AntenneHistory.jsx` | Moyenne |

## 6.2 Analyse des flux de données

### Architecture IoT simulée

Dans un déploiement réel, les antennes enverraient leurs métriques via des agents SNMP ou des collecteurs Prometheus. Dans notre plateforme, le simulateur Python remplace ces agents en générant des données statistiquement cohérentes :

```
[Antennes physiques / Simulation Python]
         │ Métriques brutes (10 min)
         ▼
  PostgreSQL — table mesures
         │ (statut = 'analyse_ia_en_cours')
         ▼
  API Flask /internal/predict
         │ Isolation Forest
         ▼
  PostgreSQL — UPDATE mesures.statut + risk_score
         │
         ▼
  React Dashboard (poll 10s)
```

### Cycle de vie d'une mesure

1. `simulation` insère une mesure avec `statut = 'analyse_ia_en_cours'`
2. `simulation` appelle `GET http://api:5000/internal/predict`
3. L'API Flask lance `run_ai_prediction()` : lit `antennes_statut`, applique Isolation Forest
4. Mise à jour de `mesures.statut` et `mesures.risk_score`
5. Mise à jour de `antennes.statut` (résumé pour accès rapide)
6. Création/résolution automatique des incidents
7. Le frontend React reçoit les données fraîches au prochain poll

## 6.3 Conception — Architecture IoT

### Modèle de dérive progressive

Le simulateur modélise l'évolution naturelle des métriques réseau par une marche aléatoire bornée (random walk with bounds). Chaque nouveau cycle utilise l'état précédent comme point de départ :

```
métrique(t) = métrique(t-1) + δ
où δ ~ Uniforme(δ_min, δ_max)
et métrique(t) ∈ [borne_inf, borne_sup]
```

Ce modèle reproduit des comportements réalistes :
- **Montée progressive de la CPU** lors d'une surcharge
- **Dégradation graduelle de la disponibilité** lors d'une panne partielle
- **Fluctuations naturelles** du signal radio selon la météo

### Modèle d'anomalies

À chaque cycle, chaque antenne a une probabilité de subir une dégradation :

| Événement | Probabilité | Effet |
|---|---|---|
| Fonctionnement normal | 93% | Dérive naturelle ±petite variation |
| Dégradation modérée (Alerte) | 5% | CPU +20-40%, latence +50-150ms, dispo -2-10% |
| Anomalie critique | 2% | CPU 85-100%, temp 80-95°C, latence 200-500ms, dispo 40-80% |

## 6.4 Réalisation

### Simulateur principal (`generate_mesures.py`)

**Initialisation avec retry automatique** :
```python
def connecter():
    """Connexion PostgreSQL avec retry automatique (20 tentatives × 3s)."""
    for attempt in range(1, 21):
        try:
            return psycopg2.connect(DATABASE_URL)
        except Exception as e:
            print(f"[DB] Tentative {attempt}/20 — {e}")
            time.sleep(3)
    raise RuntimeError("Impossible de se connecter à PostgreSQL.")
```

**Génération de métriques avec dérive progressive** :
```python
def generer_mesures(ant_type, prev=None):
    if not prev:
        # Premier cycle : état sain initial
        cpu   = random.uniform(10, 40)
        temp  = 25 + (cpu * 0.2)
        dispo = random.uniform(98.0, 100.0)
    else:
        # Cycles suivants : dérive depuis l'état précédent
        cpu   = max(0.0, min(100.0, prev['cpu']   + random.uniform(-5, 8)))
        temp  = max(15.0, min(95.0,  prev['temp']  + random.uniform(-2, 3)))
        dispo = max(40.0, min(100.0, prev['dispo'] + random.uniform(-1, 0.5)))
        
        # Injection probabiliste d'anomalies
        rand = random.random()
        if rand < 0.05:    # 5% → Alerte modérée
            cpu += random.uniform(20, 40)
            dispo -= random.uniform(2, 10)
        elif rand < 0.07:  # 2% → Anomalie critique
            cpu  = random.uniform(85, 100)
            temp = random.uniform(80, 95)
            dispo = random.uniform(40, 80)
```

**Planification avec `schedule`** :
```python
INTERVALLE_MINUTES = 10

def demarrer():
    attendre_api()          # Attend que l'API Flask soit prête
    job_simulation()        # Premier cycle immédiat
    
    schedule.every(INTERVALLE_MINUTES).minutes.do(job_simulation)
    
    while True:
        schedule.run_pending()
        time.sleep(1)
```

**Déclenchement automatique de l'IA après chaque cycle** :
```python
def job_simulation():
    # ... insertion des mesures brutes ...
    
    # Déclenche l'analyse Isolation Forest
    res = requests.get("http://api:5000/internal/predict", timeout=60)
    print(f"[IA] Analyse déclenchée — HTTP {res.status_code}")
```

### Simulation IoT — Génération initiale des antennes

Le script `generate_antennes.py` place 120 antennes avec des coordonnées GPS réelles, en respectant la géographie du littoral mahdiois (contrainte sur la longitude maximale selon la latitude pour éviter la mer) :

```python
def longitude_max_pour_latitude(lat):
    """Empêche de placer des antennes dans la Méditerranée."""
    if lat >= 35.49:  return 11.038
    elif lat >= 35.40: return 11.035
    else:             return 11.000
```

**Distribution géographique** :

| Zone | Nb antennes | Lat centre | Lon centre |
|---|---|---|---|
| Mahdia Centre | 16 | 35.504 | 11.030 |
| Hiboun | 13 | 35.520 | 11.020 |
| Ksour Essef | 13 | 35.414 | 10.980 |
| Boumerdes | 13 | 35.438 | 10.721 |
| Chebba | 13 | 35.230 | 11.000 |
| El Jem | 13 | 35.292 | 10.711 |
| Mellouleche | 13 | 35.176 | 10.990 |
| Sidi Alouane | 13 | 35.367 | 10.931 |
| Rejiche | 11 | 35.471 | 11.015 |
| **Total** | **120** | | |

### Bannière d'alertes critiques (CriticalAlertBanner.js)

Composant React global polling `/alerts/critical` toutes les 15 secondes. Affiche une bannière rouge animée lorsqu'un incident de criticité `critical` est actif, avec le nom de l'antenne, la zone et le type d'anomalie détecté par l'IA.

### Chat interne NOC (ChatWidget.js)

Interface de messagerie interne flottante permettant aux opérateurs de communiquer en temps réel. Les messages sont stockés dans la table `messages_chat` et liés aux utilisateurs authentifiés.

### Historique des métriques (AntenneHistory.jsx)

Page dédiée à la visualisation de l'évolution temporelle des métriques d'une antenne spécifique. Affiche les graphiques d'évolution de CPU, température, latence et disponibilité sur les dernières heures.

### Dockerfile du simulateur

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY entrypoint.sh .
COPY generate_antennes.py .
COPY generate_mesures.py .
RUN pip install psycopg2-binary requests schedule
RUN chmod +x entrypoint.sh
ENTRYPOINT ["./entrypoint.sh"]
```

Le `entrypoint.sh` exécute d'abord le seed des antennes (`generate_antennes.py`) puis démarre le simulateur en continu (`generate_mesures.py`).

## Conclusion

Le Sprint 4 a apporté la dimension temps réel indispensable à la démonstration de la plateforme. Le simulateur IoT reproduit fidèlement le comportement d'un réseau télécom réel, avec des dégradations progressives et des anomalies critiques sporadiques. L'intégration bout-en-bout — simulation → IA → alertes → dashboard — valide l'architecture complète de GEO-TÉLÉCOM NOC Platform.

---

# CONCLUSION GÉNÉRALE

## Résumé du projet

Ce projet de fin d'études a abouti à la réalisation de **GEO-TÉLÉCOM NOC Platform**, une plateforme complète et opérationnelle de supervision intelligente des réseaux télécoms pour le centre de Mahdia de Tunisie Télécom. La plateforme intègre cinq composants technologiques majeurs orchestrés par Docker Compose :

- **API REST Flask** (Python) avec authentification JWT et 20+ endpoints
- **Base de données PostgreSQL/PostGIS** avec schéma géospatial optimisé
- **Moteur IA Isolation Forest** (scikit-learn) pour la détection automatique d'anomalies
- **Frontend React.js** avec RBAC, dashboard temps réel et carte Leaflet interactive
- **Simulateur IoT** Python reproduisant le comportement de 120 antennes
- **Infrastructure SIG** (GeoServer) pour la dimension géographique

## Résultats obtenus

| Objectif | Résultat |
|---|---|
| Supervision temps réel | ✅ Refresh 10s, 120 antennes surveillées en continu |
| Détection IA des anomalies | ✅ Isolation Forest, score de risque 0-100, 3 niveaux de statut |
| Gestion automatique des incidents | ✅ Création et résolution automatiques par l'IA |
| Visualisation cartographique SIG | ✅ Carte Leaflet + GeoServer WMS + PostGIS |
| Contrôle d'accès RBAC | ✅ 3 rôles avec permissions granulaires |
| Rapports PDF/Excel | ✅ ReportLab + openpyxl, analyse IA incluse |
| Architecture microservices | ✅ 6 conteneurs Docker, réseau isolé, healthchecks |

## Compétences acquises

**Techniques** :
- Développement d'API REST avec Flask et architecture Blueprint
- Authentification JWT et sécurité des applications web
- Manipulation de données géospatiales (PostGIS, GeoServer, Leaflet)
- Machine Learning appliqué aux réseaux (Isolation Forest, scikit-learn)
- Conteneurisation et orchestration Docker/Docker Compose
- Développement React.js avec Context API et routing protégé

**Méthodologiques** :
- Application du framework Scrum en conditions réelles
- Modélisation UML (use cases, classes, séquences)
- Intégration continue et déploiement Dockerisé
- Documentation technique exhaustive

## Difficultés rencontrées

1. **Synchronisation PostgreSQL/PostGIS** : la configuration initiale de PostGIS dans Docker nécessitait un `start_period` suffisant dans les healthchecks pour éviter les connexions prématurées
2. **Cohérence données simulation-IA** : garantir que l'Isolation Forest ne soit déclenché qu'après l'insertion complète des mesures de tous les 120 antennes
3. **Géolocalisation réaliste** : éviter de placer des antennes en mer Méditerranée a nécessité des contraintes géographiques sur la longitude selon la latitude
4. **CORS et proxy React** : la configuration du proxy développement React vers l'API Flask a nécessité une configuration `setupProxy.js` spécifique
5. **Gestion RBAC front-back** : synchroniser les permissions entre le frontend React (routes protégées) et le backend Flask (décorateurs `@role_required`)

## Perspectives d'amélioration

1. **Modèle IA amélioré** : intégrer des modèles LSTM pour la prédiction de pannes futures basée sur l'historique temporel des métriques
2. **Collecte réelle des données** : remplacer le simulateur par des agents SNMP ou Prometheus pour la collecte de données sur équipements réels Huawei/Ericsson
3. **Alertes multi-canal** : intégrer des notifications email (SMTP), SMS (Twilio) et webhook Slack pour les incidents critiques
4. **API GraphQL** : exposer les données via GraphQL en complément du REST pour des requêtes plus flexibles
5. **Tests automatisés** : ajouter une suite de tests unitaires (pytest) et d'intégration pour garantir la fiabilité des modules IA et API
6. **Déploiement Cloud** : migrer l'infrastructure vers AWS/Azure avec Kubernetes pour la haute disponibilité et l'élasticité

---

*Rapport rédigé dans le cadre du Projet de Fin d'Études — Licence Réseaux & Télécommunications 2025/2026*
*GEO-TÉLÉCOM NOC Platform — Tunisie Télécom, Direction Régionale de Mahdia*
*Auteurs : Malek Maadi & Abir Said*
