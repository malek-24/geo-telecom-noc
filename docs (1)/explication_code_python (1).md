# Explication Détaillée des Codes Python
## Plateforme SIG de Supervision Réseau — Tunisie Telecom Mahdia

Ce document a pour but de vous aider à comprendre chaque ligne de code Python développée dans ce projet. Il vous permettra de présenter votre travail avec assurance lors de votre soutenance de PFE.

---

## Sommaire
1. [Backend API : `api/app.py`](#1-backend-api--apiapppy)
2. [Génération des Antennes : `simulation/generate_antennes.py`](#2-génération-des-antennes--simulationgenerate_antennespy)
3. [Simulation Temps Réel : `simulation/generate_mesures.py`](#3-simulation-temps-réel--simulationgenerate_mesurespy)
4. [Concepts Clés et Bibliothèques Utilisées](#4-concepts-clés-et-bibliothèques-utilisées)

---

## 1. Backend API : `api/app.py`

C'est le "cerveau" du projet. Ce script utilise **Flask** pour créer un serveur web qui expose les données de la base de données PostgreSQL/PostGIS au dashboard React.

### Points clés du code :

#### A. Initialisation et Modèle IA
```python
app = Flask(__name__)
CORS(app) # Autorise le frontend React à communiquer avec l'API
model = IsolationForest(contamination=0.1, random_state=42)
```
- **Isolation Forest** : C'est l'algorithme d'IA utilisé pour détecter les anomalies. Il "isole" les points de données qui sortent de la normale (ex: une température de 90°C alors que la moyenne est de 40°C).
- **Contamination (0.1)** : On estime qu'environ 10% des données peuvent être des anomalies.

#### B. Connexion à la Base de Données
La fonction `get_db_connection()` utilise `psycopg2` pour se connecter à PostgreSQL. Elle inclut une logique de **"Retry"** : si la base n'est pas encore prête au démarrage de Docker, le code attend 2 secondes et réessaie.

#### C. Les Endpoints (Routes)
1.  **`/antennes` (GET)** :
    - Récupère toutes les antennes depuis la table `antennes`.
    - Jointure avec la table `mesures` pour obtenir le dernier état (Température, CPU).
    - Utilise `ST_AsGeoJSON(geom)` de PostGIS pour envoyer les coordonnées directement au format cartographique.
2.  **`/predict` (POST/GET)** :
    - C'est ici que l'IA intervient. 
    - Le code récupère les dernières mesures, les transforme en un tableau `pandas`.
    - Le modèle fait une prédiction : `1` pour normal, `-1` pour anomalie.
    - Si l'IA détecte `-1`, l'antenne est marquée en rouge sur la carte.
3.  **`/stats` (GET)** :
    - Calcule des agrégats (Nombre total d'antennes, nombre d'alertes).
    - Très utile pour les compteurs en haut du dashboard.

---

## 2. Génération des Antennes : `simulation/generate_antennes.py`

Ce script permet de peupler la base de données avec des antennes fictives mais géographiquement réalistes pour le gouvernorat de Mahdia.

### Logique de "Terre vs Mer" (Le défi technique) :
Une des parties les plus importantes que vous avez corrigées est la contrainte géographique.
```python
def max_longitude_for_lat(lat):
    if lat >= 35.49: return 11.044 # Nord (Mahdia Ville)
    elif lat >= 35.40: return 11.040 # Centre (Rejiche)
    ...
```
- **Pourquoi ?** Mahdia est une ville côtière. Si on génère des points au hasard, certaines antennes tomberaient dans la mer Méditerranée.
- **Solution** : Nous avons défini une limite de longitude qui dépend de la latitude. Si un point généré dépasse cette limite (trop à l'Est), le script le rejette et en génère un nouveau sur terre.

---

## 3. Simulation Temps Réel : `simulation/generate_mesures.py`

Ce script tourne en boucle pour simuler des capteurs IoT sur chaque antenne.

### Fonctionnement :
1.  Il récupère la liste de toutes les antennes dans la base.
2.  Toutes les **60 secondes**, il génère des valeurs pour chaque antenne :
    - **Température** : Entre 30°C et 50°C (normal) ou > 70°C (anomalie).
    - **Charge CPU** : Entre 10% et 90%.
3.  **Injection d'anomalies** : Le code a une probabilité de 5% de générer une "panne" (valeurs extrêmes) pour tester le système d'alerte et l'IA.

---

## 4. Concepts Clés et Bibliothèques Utilisées

Pour votre présentation, voici ce qu'il faut dire sur les outils utilisés :

-   **Flask** : Framework "Micro" pour Python. Choisi pour sa légèreté et sa facilité à créer des API REST rapidement.
-   **Psycopg2** : Le connecteur standard pour PostgreSQL. Indispensable pour exécuter des requêtes SQL depuis Python.
-   **Pandas** : Bibliothèque de manipulation de données. Utilisée ici pour préparer les données avant de les donner à l'IA.
-   **Scikit-Learn** : La bibliothèque de référence pour le Machine Learning en Python. C'est elle qui fournit l'algorithme `Isolation Forest`.
-   **Docker-Compose** : Permet de lancer l'API et ses scripts de simulation en un seul bloc, garantissant que tout le monde (développeurs ou superviseurs) aura le même environnement.

---

## 5. La Base de Données : PostgreSQL + PostGIS

Le projet utilise **PostGIS**, qui est une extension spatiale pour PostgreSQL. Elle permet de stocker des points géographiques au lieu de simples chiffres.

### Pourquoi c'est important ?
Dans `init.sql`, nous définissons un champ `geom` de type `GEOMETRY(Point, 4326)`.
- **4326** : C'est le code standard pour les coordonnées GPS (WGS84).
- **Triggers SQL** : J'ai mis en place un "Trigger" qui calcule automatiquement la géométrie dès qu'on insère une latitude et une longitude. Cela garantit que la carte sera toujours synchronisée avec les données.

### Conseil pour la soutenance :
Expliquez que l'utilisation de PostGIS permet de faire des calculs spatiaux complexes (comme "quelles sont les antennes à moins de 5km de ce point ?") directement dans la base de données, ce qui est beaucoup plus rapide que de le faire en Python.

### Note sur `scripts/gen_word.py` :
C'est un script utilitaire que j'ai créé pour transformer le rapport au format Markdown en un fichier Word professionnel (`.docx`). Il utilise `python-docx` pour gérer la mise en page, les titres et les tableaux automatiquement.


### Conseil pour la soutenance :
Si le jury vous demande : *"Pourquoi avez-vous utilisé Isolation Forest plutôt qu'un simple seuil (if Temp > 70) ?"*
**Réponse** : *"Les seuils statiques sont limités. L'IA peut détecter des pannes complexes où la température est normale mais le CPU est anormalement bas, ou une combinaison de plusieurs facteurs qui sort de l'ordinaire."*
