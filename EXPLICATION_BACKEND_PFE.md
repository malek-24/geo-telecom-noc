# Explication du Code Backend (Flask / Python) - Plateforme NOC

Ce document détaille l'architecture et le code côté serveur (Backend) de la plateforme. Il est conçu pour vous aider à justifier vos choix techniques devant le jury de soutenance.

---

## 1. Architecture Globale (API RESTful avec Flask)

Le backend a été développé en **Python** en utilisant le micro-framework **Flask**. Il ne génère aucune page HTML (c'est le rôle de React). Son seul rôle est d'exposer une **API RESTful**.
Le fichier principal est **`api/app.py`**.

- **Endpoints** : L'application met à disposition des "routes" (comme `/incidents` ou `/api/commentaires`) que le frontend interroge en envoyant et recevant des données au format **JSON**.
- **Avantage** : Cette séparation totale (Backend API d'un côté, Frontend SPA de l'autre) est le standard actuel de l'industrie pour créer des applications performantes et évolutives.

---

## 2. Sécurité et Authentification (JWT & RBAC)

La gestion des utilisateurs repose sur deux piliers : le **hachage des mots de passe** et les **Jetons JWT**.

1. **Bcrypt** : Les mots de passe des utilisateurs (Admin, Techniciens, etc.) ne sont jamais stockés en clair dans la base de données. Ils sont chiffrés à l'aide de la librairie `werkzeug.security` (génération de *hash*).
2. **JWT (JSON Web Token)** : Quand un utilisateur se connecte, la fonction `/login` lui génère un jeton cryptographique contenant son ID et son Rôle. Ce jeton a une durée de vie (24 heures).
3. **Décorateur `@token_required`** : J'ai codé un décorateur Python (une fonction qui "enveloppe" les routes API) qui vérifie à chaque requête si le jeton JWT envoyé par le frontend est valide et s'il a le bon rôle. S'il n'est pas bon, l'API renvoie une erreur `403 Forbidden` ou `401 Unauthorized`.

---

## 3. Le Modèle d'Intelligence Artificielle (Isolation Forest)

Au cœur de la plateforme réside la détection d'anomalies. Elle n'est pas gérée par des règles "Si/Sinon" basiques, mais par du Machine Learning.

- **Algorithme** : Nous utilisons **Isolation Forest** (importé depuis `scikit-learn`). C'est un algorithme "Non Supervisé" parfait pour la détection d'anomalies (Outliers).
- **Fonctionnement dans le code** : 
  1. L'algorithme extrait les indicateurs (Température, CPU, RAM, Latence, Trafic) depuis la base de données.
  2. Il construit une forêt d'arbres décisionnels aléatoires.
  3. Les données "anormales" (ex: une température très élevée combinée à une forte latence) sont plus "faciles à isoler" et ont un chemin court dans l'arbre. Elles sont alors étiquetées comme anomalies (`-1`) avec un "Risk Score".
- **Auto-Guérison** : Lorsque le technicien déclare le problème comme "Réglé", le code déclenche automatiquement (`_run_prediction`) un recalibrage du modèle IA pour que l'antenne redevienne saine.

---

## 4. Le Moteur de Simulation Réseau

Le backend intègre également un script autonome de simulation (`simulation/generate_mesures.py`).
- **Pourquoi ?** Dans un projet PFE, il est très difficile d'obtenir des données en direct depuis de vraies antennes télécoms.
- **Comment ?** Nous utilisons des boucles infinies qui génèrent des relevés de température et de trafic *réalistes* (avec des variations aléatoires normales, et parfois des "pics" provoquant artificiellement des incidents) pour 127 antennes de Mahdia toutes les minutes.

---

## 5. Interaction avec PostgreSQL (Base de données)

Contrairement à l'utilisation d'un ORM lourd comme SQLAlchemy, nous avons opté pour le driver natif **`psycopg2`**.
- Les requêtes SQL sont écrites "à la main" (`SELECT`, `INSERT`, `UPDATE`).
- **Avantage** : Cela permet d'avoir des requêtes ultra-optimisées, particulièrement importantes pour manipuler les milliers de lignes générées par le simulateur et pour l'intégration avec **PostGIS** (requêtes spatiales géographiques).

---

### 💡 Conseils pour la soutenance (Questions du Jury) :

**Question possible :** *"Pourquoi avoir choisi Flask plutôt que Django ou Node.js/Express ?"*

**Réponse idéale :** *"Flask est un 'micro-framework' en Python. Contrairement à Django qui est très lourd et impose sa propre structure, Flask nous a permis de créer une API REST très légère et réactive. De plus, le choix de Python s'imposait naturellement car c'est le langage dominant pour la Data Science et le Machine Learning. Intégrer notre modèle Scikit-Learn (Isolation Forest) directement dans une API Python est beaucoup plus simple et performant que d'essayer de le faire communiquer avec un backend Node.js (JavaScript)."*

**Question possible :** *"Comment s'assure-t-on que l'API ne fige pas pendant le calcul de l'Intelligence Artificielle ?"*

**Réponse idéale :** *"Le calcul IA (`_run_prediction`) est exécuté dans un Thread Python en arrière-plan (`threading.Thread(target=_run_prediction).start()`). Ainsi, lorsqu'un utilisateur clique sur 'Résoudre un incident', l'API lui répond 'OK' instantanément (en quelques millisecondes) sans attendre que le recalibrage de l'IA (qui peut prendre plusieurs secondes sur un gros dataset) soit terminé."*
