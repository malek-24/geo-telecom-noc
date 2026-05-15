# Explication du Modèle IA (Intelligence Artificielle) - Plateforme NOC

Ce document est entièrement dédié au moteur d'Intelligence Artificielle de la plateforme. C'est l'un des points les plus valorisants de votre PFE, car il transforme un simple tableau de bord en un outil "intelligent" et proactif.

---

## 1. Le Choix du Modèle : Pourquoi "Isolation Forest" ?

Dans la gestion des réseaux télécoms (NOC), les pannes graves sont heureusement rares par rapport au fonctionnement normal. Nous cherchons donc à détecter des "anomalies" ou des "comportements déviants".

- **Le problème des règles fixes (If/Else)** : Si nous utilisions une simple règle comme `Si Température > 75°C ALORS Alerte`, le système serait aveugle aux pannes complexes (ex: la température est normale à 60°C, mais le trafic est nul et la latence est très élevée).
- **Apprentissage Non Supervisé (Unsupervised Learning)** : Nous n'avons pas de base de données d'exemples de pannes exactes pour entraîner l'IA (donc pas de Réseaux de Neurones classiques). Nous donnons simplement au modèle l'état actuel du réseau, et il doit deviner seul ce qui "sort de l'ordinaire".
- **Isolation Forest** (Forêt d'Isolement) est l'algorithme le plus performant au monde pour la détection d'anomalies (Outlier Detection).

---

## 2. Comment fonctionne l'algorithme ?

L'algorithme Isolation Forest (importé depuis la librairie `scikit-learn` en Python) fonctionne d'une manière très visuelle :

1. L'IA sélectionne aléatoirement une caractéristique (ex: la Température).
2. Elle coupe les données en deux de manière aléatoire (ex: toutes les températures supérieures à 50 d'un côté, et inférieures de l'autre).
3. Elle répète cette opération en créant des "branches" (un arbre de décision).
4. **Le concept clé** : Les valeurs normales sont très nombreuses et regroupées au centre. Il faut donc beaucoup de "coupes" pour les isoler individuellement. À l'inverse, **une anomalie extrême est isolée très rapidement**, avec très peu de coupes (elle se trouve près de la racine de l'arbre).
5. L'algorithme calcule un "Score de Risque". Plus une antenne est isolée rapidement, plus son score est élevé, et elle est déclarée comme **Anomalie**.

---

## 3. Les Variables Analysées (Features)

Pour chaque antenne, l'IA analyse simultanément 6 variables métriques (Features) pour trouver des corrélations anormales :
- **Température** (°C)
- **CPU** (%)
- **RAM** (%)
- **Latence** (ms)
- **Perte de paquets / Packet Loss** (%)
- **Trafic / Débit** (Mbps)

---

## 4. Implémentation Technique dans le Code (`api/app.py`)

Voici comment le modèle a été programmé dans le backend :

1. **Extraction (Pandas)** : Nous utilisons `pandas` pour extraire les dernières mesures réseau depuis PostgreSQL et les transformer en tableau mathématique (DataFrame).
2. **Entraînement Dynamique (`fit_predict`)** : Le modèle n'est pas pré-entraîné. Il s'entraîne en temps réel sur les données actuelles du réseau. Ainsi, si tout le réseau subit une canicule estivale (la température moyenne passe de 40°C à 50°C pour toutes les antennes), l'IA s'adapte et comprend que c'est le "nouveau normal", évitant ainsi les fausses alertes.
3. **Création d'Incidents Automatique** : Si le résultat de l'IA (la prédiction) est `-1` (Anomalie), le code Python insère automatiquement un nouveau ticket dans la table `incidents` de la base de données, avec la mention "Généré par Isolation Forest".
4. **Threading** : Le calcul IA est lancé de manière asynchrone (dans un thread en arrière-plan) pour ne pas bloquer les autres requêtes de l'application pendant le calcul mathématique.

---

## 5. Explication des Hyperparamètres (Configuration IA)

Dans le code, le modèle est instancié ainsi :
`IsolationForest(contamination=0.03, random_state=42)`

- **Contamination = 0.03 (3%)** : C'est le paramètre le plus important. On indique à l'IA qu'on estime qu'il y a environ 3% d'antennes en panne sur l'ensemble du réseau. L'IA va donc isoler les 3% d'antennes qui ont le comportement le plus étrange.
- **Random_state** : Assure que les calculs aléatoires du modèle donnent toujours le même résultat si on leur fournit exactement les mêmes données.

---

### 💡 Conseils pour la soutenance (Questions du Jury) :

**Question possible :** *"Pourquoi ne pas avoir utilisé un réseau de neurones (Deep Learning) pour détecter les anomalies ?"*

**Réponse idéale :** *"Le Deep Learning nécessite d'énormes quantités de données historiques déjà étiquetées (labelisées 'Panne' ou 'Normal') pour s'entraîner correctement, ce que l'on appelle l'apprentissage supervisé. Dans notre cas, les pannes sont imprévisibles et varient constamment. L'Isolation Forest est un algorithme de Machine Learning non-supervisé, beaucoup plus léger, rapide (adapté au temps réel) et qui ne nécessite pas de données étiquetées pour repérer une anomalie inédite."*

**Question possible :** *"Que se passe-t-il quand un technicien répare l'antenne sur le terrain ?"*

**Réponse idéale :** *"L'IA est couplée au système de commentaires. Lorsqu'un technicien ou un modérateur déclare l'incident comme 'Réglé' sur l'application, cela déclenche automatiquement un nouveau cycle d'entraînement asynchrone de l'Isolation Forest. L'IA recalcule l'état de tout le réseau en ignorant l'ancienne anomalie, et l'antenne repasse au vert sur la carte instantanément."*
