# CHAPITRE 6 : SPRINT 4 — IoT ET SIMULATION

## Introduction du chapitre

Un NOC ne peut fonctionner sans flux de mesures continu. En environnement de production, ces flux proviennent des équipements réseau et des sondes. Pour le PFE, un **simulateur** génère des métriques réalistes toutes les 3 secondes, et un **prototypage IoT** (Arduino Uno + DHT11) alimente le site « ISET Mahdia » en température réelle. Ce chapitre décrit l'architecture, les algorithmes de simulation et l'intégration avec l'API Flask.

---

## 6.1 Objectifs du sprint

- Maintenir un réseau « vivant » en démonstration ;
- Éviter les anomalies aléatoires non contrôlées ;
- Permettre des scénarios de test reproductibles (admin, capteur, test-ia) ;
- Documenter le flux bout-en-bout jusqu'à l'IA.

---

## 6.2 Architecture IoT et simulation

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────┐
│ generate_mesures│────►│ PostgreSQL       │────►│ /internal/  │
│ (MRRW, 3 s)     │     │ table mesures    │     │ predict     │
└─────────────────┘     └──────────────────┘     └──────┬──────┘
┌─────────────────┐                                    │
│ Arduino DHT11   │──► serial_bridge.py ──► POST /iot/mesure
└─────────────────┘
```

**Figure 6.1 : Architecture du flux de simulation**

*Source : Réalisation personnelle.*

---

## 6.3 Génération des données simulées

Le conteneur `simulation` exécute `generate_mesures.py` selon un planning (`schedule`). Chaque cycle parcourt les antennes actives (sauf ISET Mahdia, réservée au capteur réel).

---

## 6.4 Simulation des métriques — Mean-Reverting Random Walk

**Formule MRRW :**

\[
v_{t+1} = v_t + \alpha \cdot (cible - v_t) + \mathcal{N}(0, \sigma)
\]

avec \(\alpha = 0{,}15\) et des cibles : T=28°C, CPU=40%, RSSI=-65 dBm, latence=15 ms, disponibilité=99%.

**Tableau 6.1 — Paramètres MRRW**

| Paramètre | Valeur |
|-----------|--------|
| Intervalle global | 3 s |
| ALPHA | 0.15 |
| Anomalies aléatoires | **Désactivées** |

**Figure 6.2 : Courbe Mean-Reverting Random Walk (concept)**

[Insérer graphique : température stable avec bruit léger]

**Analyse :** Le MRRW produit des courbes réalistes pour la soutenance, sans sauts brutaux inexpliqués. Les anomalies apparaissent uniquement par action volontaire, ce qui facilite la narration devant le jury.

---

## 6.5 Flux temps réel

1. INSERT mesure en base ;
2. Appel HTTP `GET http://api:5000/internal/predict?antenne_id=X` ;
3. Mise à jour statut et éventuel incident ;
4. Frontend polling 15 s affiche le changement.

---

## 6.6 Communication avec Flask

`iot_routes.py` expose `POST /iot/mesure` protégé par clé API (`IOT_API_KEY`). Le corps JSON contient `antenne_id` ou lookup par nom, température, etc. Le pipeline IA est identique au simulateur.

---

## 6.7 Interaction avec l'IA

Le simulateur n'implémente aucune logique d'anomalie : il délègue à `prediction.py`. Cette séparation respecte le principe **single responsibility** et garantit un comportement identique quelle que soit la source de données.

---

## 6.8 Prototypage Arduino

**Figure 6.3 : Pont série Arduino — antenne ISET**

[Insérer photo : Arduino + DHT11 ou schéma]

Le fichier `arduino_uno_dht11_iset.ino` lit la température. `serial_bridge.py` publie vers l'API. Chauffer le capteur provoque une anomaly détectée par IF — démonstration physique appréciée en soutenance.

---

## 6.9 Résultats

**Figure 6.4 : Séquence temporelle des mesures en base**

[Insérer capture : pgAdmin ou requête ORDER BY date_mesure DESC]

L'observation confirme un flux régulier, des statuts majoritairement normaux, et des pics corrélés aux tests manuels.

---

## Conclusion du chapitre 6

Le sprint 4 assure la **vivacité** de la plateforme et la **reproductibilité** des démonstrations. La simulation MRRW et l'IoT DHT11 complètent le cycle données → IA → interface, validant l'architecture bout-en-bout du PFE.

---

*Fin du chapitre 6 — environ 10 pages.*
