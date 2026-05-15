# Explication du Code Frontend (React.js) - Plateforme NOC

Ce document explique en détail le fonctionnement du code de l'interface graphique (Frontend) que nous avons développée. Il est conçu pour vous aider à comprendre l'architecture et à répondre facilement aux questions du jury lors de la soutenance.

---

## 1. Architecture Globale (React.js)

Le frontend est développé avec **React.js**. C'est une SPA (Single Page Application) : l'application ne recharge jamais complètement la page web quand on navigue entre les menus. Cela offre une fluidité similaire à une application de bureau.

Le code est divisé en plusieurs parties dans le dossier `src/` :
- `components/` : Les petits blocs réutilisables (ex: le menu `Sidebar.js`).
- `pages/` : Les vues complètes (ex: `Dashboard.js`, `MapPage.js`, `ModerationPage.js`).
- `auth/` : La gestion de la connexion, des rôles (Admin, Modérateur, Technicien) et la protection des routes.
- `styles/` : L'apparence visuelle.

---

## 2. Communication avec le Backend (Axios et JWT)

Le fichier clé ici est **`apiConfig.js`**.
Nous utilisons la bibliothèque **Axios** pour parler avec notre API Flask.

### Comment ça marche ? (L'Intercepteur)
Lorsqu'un utilisateur se connecte, l'API lui donne un "Jeton" de sécurité (JWT). Nous stockons ce jeton dans le navigateur (`localStorage`).
Dans `apiConfig.js`, nous avons codé un **Intercepteur** : avant chaque requête (pour récupérer les antennes ou les incidents), Axios "intercepte" la requête et ajoute automatiquement le Jeton JWT dans l'en-tête (Header) d'Autorisation. 
Ainsi, l'API sait toujours qui fait la requête et quel est son rôle, de manière hautement sécurisée.

---

## 3. La Cartographie (Leaflet et GeoServer)

La page **`MapPage.js`** est le cœur de la supervision géographique. Nous utilisons **React-Leaflet**, une bibliothèque open-source de cartographie très légère et performante.

### Intégration WMS
Sur cette carte, nous n'affichons pas seulement les points des antennes. Nous avons connecté la carte à notre serveur **GeoServer** via le protocole standard **WMS (Web Map Service)**. 
- GeoServer lit les données dans PostgreSQL/PostGIS.
- Il dessine des "tuiles" (images de carte) avec les zones des antennes.
- Leaflet superpose ces images dynamiques par-dessus la carte de base (OpenStreetMap).
- En même temps, nous récupérons les données en direct depuis l'API Flask pour dessiner des marqueurs dynamiques (verts, oranges, rouges) selon l'état de santé de chaque antenne détecté par l'IA.

---

## 4. Actualisation en Temps Réel (Polling)

Dans le composant **`Dashboard.js`**, nous utilisons les "Hooks" React (notamment `useEffect`).
Nous avons programmé un minuteur (`setInterval`) qui exécute la fonction de récupération des données de l'API **toutes les 30 secondes**.
Grâce au fonctionnement de React, lorsque les nouvelles données arrivent, seules les parties de l'écran qui ont changé (comme un chiffre de température ou la couleur d'une carte KPI) sont redessinées, sans figer l'écran de l'utilisateur.

---

## 5. Le Design System (UI/UX)

Tout le design repose sur les **Variables CSS** définies dans `styles.css`.
- Au lieu de mettre des couleurs en dur partout, nous utilisons des variables comme `var(--accent)` (Indigo) ou `var(--surface)` (Blanc).
- Cela nous a permis d'implémenter un design moderne "Glassmorphism" et épuré, très facilement modifiable.
- Si le jury demande pourquoi l'interface est si claire : "C'est parce que nous avons étudié l'UX (Expérience Utilisateur) des salles de contrôle NOC, où les opérateurs travaillent 8h par jour sur l'écran. Il fallait réduire la fatigue visuelle tout en mettant en évidence (en rouge vif) les incidents critiques."

---

## 6. Workflow de Modération (Unification)

La page **`ModerationPage.js`** est intelligente. Elle s'adapte au rôle de l'utilisateur (Technicien ou Admin/Modérateur).
- Grâce aux données du JWT, le composant sait qui regarde la page.
- Si c'est le technicien, il voit les incidents et peut "Ajouter un commentaire", mais il ne peut pas modifier la plateforme.
- Si c'est l'administrateur, un bouton caché apparaît pour valider ou rejeter ces interventions.

---

### 💡 Conseils pour la soutenance (Questions du Jury) :

**Question possible :** *"Pourquoi avoir choisi React.js au lieu de faire du simple HTML/JavaScript avec Django ou Flask (Templates) ?"*

**Réponse idéale :** *"Dans un NOC (Network Operations Center), la vitesse d'actualisation est primordiale. Si nous utilisions des templates HTML classiques, toute la page devrait clignoter et se recharger à chaque nouvel incident ou à chaque nouvelle température. Avec React, le DOM virtuel (Virtual DOM) permet de ne mettre à jour que le chiffre de température de l'antenne spécifique, instantanément. De plus, React nous a permis de séparer proprement le Backend et le Frontend pour de meilleures performances de développement."*
