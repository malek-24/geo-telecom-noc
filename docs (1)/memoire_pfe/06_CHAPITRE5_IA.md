# CHAPITRE 5 : SPRINT 3 — INTELLIGENCE ARTIFICIELLE

## Introduction du chapitre

L'intelligence artificielle constitue la valeur ajoutée distinctive de la plateforme. Ce chapitre documente de manière approfondie le pipeline de détection d'anomalies : des capteurs (ou de la simulation) jusqu'à l'affichage des statuts sur le dashboard et la carte. L'algorithme retenu est **Isolation Forest**, implémenté avec **Scikit-learn** dans le module `api/ia/`.

---

## 5.1 Objectifs du sprint

- Sélectionner un algorithme non supervisé adapté aux rares anomalies ;
- Entraîner et persister un modèle sur l'historique de mesures normales ;
- Classifier chaque nouvelle mesure en normal / alerte / critique ;
- Créer automatiquement des incidents lorsque nécessaire ;
- Intégrer le pipeline aux routes `/predict`, `/internal/predict` et au simulateur.

---

## 5.2 IA appliquée aux télécommunications

Les réseaux radio exhibent des corrélations entre variables physiques et d'usage. Une hausse de température en baie peut précéder une dégradation CPU ; une baisse de disponibilité peut coïncider avec une latence élevée. Les méthodes multivariées captent ces signatures mieux que des seuils isolés.

L'apprentissage **non supervisé** est pertinent car les anomalies réelles sont rares et hétérogènes : il est plus réaliste d'apprendre le « comportement normal » du parc que de lister toutes les pannes possibles.

---

## 5.3 Analyse des données

**Tableau 5.1 — Variables d'entrée du modèle**

| Variable | Unité | Plage typique normale |
|----------|-------|------------------------|
| temperature | °C | 25–32 |
| cpu | % | 36–44 |
| signal (RSSI) | dBm | -71 à -59 |
| latence | ms | 13,5–16,5 |
| disponibilite | % | 97–100 |

Des features géographiques dérivées (`delta_*_voisins`, `nb_voisins_anomalies`) enrichissent le contexte spatial via `geo_context.py`.

---

## 5.4 Prétraitement

1. Extraction des 2000 dernières mesures étiquetées normales (fenêtre glissante) ;
2. Enrichissement géographique ;
3. **StandardScaler** (moyenne nulle, variance unitaire) ;
4. Gestion du cas démarrage à froid : jeu synthétique si peu d'historique (`_fallback_synthetique`).

---

## 5.5 Détection d'anomalies

Le pipeline `train_and_predict` dans `model.py` :

1. Charge ou entraîne Isolation Forest ;
2. Produit `predict` (-1 = anomalie) et `decision_function` ;
3. Transmet les scores au module `scoring.py` pour conversion en score de santé 0–100 ;
4. Applique `determine_statuts_dynamiques` pour le statut métier.

---

## 5.6 Étude des algorithmes envisagés

| Algorithme | Avantages | Inconvénients | Retenu |
|------------|-----------|---------------|--------|
| Seuils statiques | Simple | Faux positifs | Non |
| k-means | Rapide | k fixe, sphérique | Non |
| LOF | Local | Coût calcul | Non |
| **Isolation Forest** | Haute dimension, peu de paramètres | Boîte noire partielle | **Oui** |
| Autoencodeur | Expressif | Besoin GPU, complexité | Non |

---

## 5.7 Isolation Forest — principe

Isolation Forest isole les points en choisissant aléatoirement une feature et une valeur de coupure. Les anomalies, étant rares et différentes, sont isolées en peu de divisions. Le **score de décision** reflète la profondeur moyenne d'isolation.

---

## 5.8 Justification du choix

- Données majoritairement normales : correspond à l'hypothèse IF ;
- Dimension modeste (5 à 10 features) : performant ;
- Bibliothèque **Scikit-learn** mature, intégration Python/Flask native ;
- Réentraînement périodique possible (24 h ou 100 mesures normales).

**Tableau 5.3 — Paramètres Isolation Forest**

| Paramètre | Valeur |
|-----------|--------|
| n_estimators | 200 |
| contamination | 0.005 |
| random_state | 42 |
| max_samples train | 2000 |

---

## 5.9 Architecture IA

**Figure 5.1 : Pipeline IA — de la mesure au statut**

```
Mesure INSERT → prediction.py → model.train_and_predict
    → scoring (santé 0-100) → statut (normal/alerte/critique)
    → UPDATE mesures + antennes → incident si critique
    → historique_etats + audit
```

*Source : Réalisation personnelle.*

---

## 5.10 Entraînement du modèle

Le modèle et le scaler sont sérialisés (`joblib`) dans `/tmp/iso_forest_model.pkl`. Le réentraînement est déclenché par le simulateur ou manuellement (`POST /ia/retrain`). Le flag `force_no_retrain` protège les démonstrations admin.

---

## 5.11 Évaluation

Métriques qualitatives en environnement de test :

- **Taux de faux positifs** observé faible après réglage contamination ;
- **Temps de traitement** < 500 ms pour une antenne ;
- **Cohérence métier** : validation par l'encadrant sur scénarios chauffe DHT11 et injection admin.

Une évaluation quantitative exhaustive (matrice de confusion sur jeu étiqueté) constitue une perspective si un historique d'incidents étiquetés devient disponible.

---

## 5.12 Classification des états

**Tableau 5.2 — Seuils de classification**

| Statut | Score santé indicatif | Couleur UI |
|--------|----------------------|------------|
| normal | ≥ seuil normal | Vert |
| alerte | intermédiaire | Orange |
| critique | faible | Rouge |

Le module `diagnostics.py` génère un texte explicatif (type d'anomalie) stocké dans l'incident.

---

## 5.13 Intégration Flask

- `GET /predict?antenne_id=` : analyse une antenne ;
- `GET /internal/predict` : appel interne simulateur sans JWT public ;
- `POST /api/test-ia` : scénario de test jury.

---

## 5.14 Intégration React

Les pages consomment le champ `statut` et `risk_score` renvoyés par `GET /antennes`. Aucun calcul IA côté client : respect de la logique métier centralisée.

---

## 5.15 Affichage des résultats

**Figure 5.2 : Sites en état normal**

[Insérer capture : carte dominante verte]

**Analyse :** L'état normal reflète un réseau sain ; c'est l'état par défaut après bootstrap.

**Figure 5.3 : Sites en alerte**

[Insérer capture : marqueurs orange]

**Analyse :** L'alerte signale une dérive détectée par IF sans criticité maximale — l'opérateur surveille.

**Figure 5.4 : Sites critiques**

[Insérer capture : marqueurs rouges + bannière]

**Figure 5.5 : Résultats IA sur le Dashboard**

[Insérer capture : KPI alertes/critiques > 0]

**Figure 5.6 : Création automatique d'incident**

[Insérer capture : incident source Isolation Forest]

---

## 5.16 Analyse des résultats

Lors d'une injection de température élevée sur une antenne test, le pipeline :

1. Marque la mesure en analyse ;
2. Calcule un score de santé dégradé ;
3. Passe le statut à alerte puis critique si persistant ;
4. Crée un incident avec `source_detection = 'Isolation Forest'` ;
5. Enregistre l'audit et l'historique d'état.

Ce comportement satisfait le cahier des charges de démonstration.

---

## 5.17 Limites rencontrées

- **Explicabilité partielle** : IF ne fournit pas de règles lisibles comme un arbre de décision ;
- **Dépendance à la qualité des données** : mesures manquantes nécessitent filtrage SQL ;
- **Réentraînement** : en production réelle, gouvernance des versions de modèle indispensable ;
- **Pas de prédiction temporelle** : détection instantanée, pas de forecast 24 h (perspective LSTM).

---

## Conclusion du chapitre 5

Le module IA transforme la plateforme d'un simple outil de visualisation en système de supervision proactive. Isolation Forest, couplé au scoring métier et à la création d'incidents, répond à la problématique initiale de réduction du temps de détection. Le chapitre suivant détaille l'alimentation continue des données via simulation et IoT.

---

*Fin du chapitre 5 — environ 18 pages.*
