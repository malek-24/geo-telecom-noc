# Explication Détaillée du Frontend (React.js)
## Plateforme SIG de Supervision Réseau — Tunisie Telecom Mahdia

Ce document explique le fonctionnement de l'interface utilisateur. Le frontend est construit avec **React.js**, une bibliothèque moderne pour créer des interfaces dynamiques et réactives.

---

## 1. Architecture des Composants

Le projet utilise une architecture modulaire. Chaque partie de l'écran est un "Composant" réutilisable :

-   **`Sidebar.js`** : La barre de navigation latérale.
-   **`Topbar.js`** : Affiche le titre de la page et l'heure en temps réel.
-   **`NetworkMap.js`** : Le composant le plus complexe qui gère la carte interactive.
-   **`StatsCard.js`** : Les petits blocs affichant les chiffres (Total, Alertes).

---

## 2. Le Coeur de la Carte : `NetworkMap.js`

C'est ici que la magie du SIG opère. Nous utilisons la bibliothèque **Leaflet**.

### Fonctionnalités avancées :

#### A. Récupération des données (Fetching)
Nous utilisons le "Hook" `useEffect` pour appeler l'API Python toutes les 60 secondes.
```javascript
useEffect(() => {
  const fetchData = async () => {
    const res = await fetch('http://localhost:5000/antennes');
    const data = await res.json();
    setAntennas(data);
  };
  fetchData();
  const interval = setInterval(fetchData, 60000); // Auto-refresh 60s
  return () => clearInterval(interval);
}, []);
```

#### B. Algorithme de la Fibre (MST - Minimum Spanning Tree)
Le code calcule automatiquement le chemin le plus court pour relier toutes les antennes entre elles par la fibre optique. Cela utilise l'algorithme de **Prim**. 
*Pourquoi ?* Pour simuler le réseau "Backbone" de Tunisie Telecom sans avoir à dessiner chaque ligne manuellement.

#### C. Analyse de Couverture (Zones blanches)
Le code divise Mahdia en une grille. Pour chaque point de la grille, il vérifie s'il y a une antenne à moins de 10 km. S'il n'y en a pas, il marque une **"Zone sous-couverte"**. C'est une fonctionnalité d'aide à la décision pour TT pour savoir où installer la prochaine antenne.

#### D. Panel IA (Chatbot)
Sur le côté de la carte, un panel affiche des recommandations textuelles basées sur les données. Si une anomalie est détectée, le panel "AI Insight" explique le problème à l'utilisateur.

---

## 3. Design et Esthétique (CSS)

Le style utilisé est le **Glassmorphism** (Effet de verre).
- **Fond sombre** : Pour réduire la fatigue oculaire des techniciens qui surveillent les écrans toute la journée.
- **Couleurs sémantiques** : 
    - 🟢 Vert : Tout va bien.
    - 🟡 Jaune : Attention (Alerte).
    - 🔴 Rouge : Panne critique (IA ou seuil dépassé).
    - 🟣 Violet : Suggestion de l'IA pour une nouvelle antenne.

---

## 4. Concepts Clés à retenir pour la présentation

-   **React Hooks (`useState`, `useEffect`)** : Utilisés pour gérer l'état des données et le cycle de vie des composants.
-   **Leaflet.js** : La bibliothèque cartographique leader. Elle est légère et permet d'ajouter des marqueurs, des lignes et des popups facilement.
-   **Temps Réel (Polling)** : L'application ne nécessite pas de rafraîchir la page. Elle se met à jour toute seule toutes les minutes grâce à `setInterval`.
-   **Responsive Design** : L'interface s'adapte à la taille de l'écran (Tablette, PC, Grand écran de salle de supervision).

### Question possible du jury :
*"Comment gérez-vous le temps réel dans votre application ?"*
**Réponse** : *"J'ai implémenté un système de 'Polling' (interrogation cyclique) à 60 secondes. Le frontend React interroge l'API Flask à intervalle régulier, et grâce au 'Virtual DOM' de React, seule la partie de la carte qui change est mise à jour, sans recharger toute la page."*
