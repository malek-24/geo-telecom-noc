# CHAPITRE 4 : SPRINT 2 — DÉVELOPPEMENT FRONTEND

## Introduction du chapitre

Le deuxième sprint a livré l'interface utilisateur de la plateforme NOC : application **React 18** organisée en pages métier, communication avec l'API via **Axios**, visualisations **Recharts** et cartographie **Leaflet**. Ce chapitre constitue le cœur ergonomique du mémoire : il documente chaque module visible par les opérateurs du centre de Mahdia, avec analyse des captures d'écran et références aux figures.

Comme illustré dans la structure du projet, le frontend n'utilise pas TypeScript ni Tailwind dans la version livrée ; le style repose sur des **feuilles CSS** modulaires (`styles.css`, `DashboardStyles.css`, `MapStyles.css`, etc.) et un **design system** à variables CSS (palette bleue NOC, cartes blanches, sidebar sombre).

---

## 4.1 Objectifs du sprint

- Proposer une navigation cohérente via `Sidebar` et `react-router-dom` ;
- Implémenter le tableau de bord, la carte, les antennes et les incidents ;
- Intégrer l'authentification (contexte React `AuthContext`) ;
- Assurer le rafraîchissement automatique silencieux des données ;
- Livrer les modules administration, audit, messagerie et rapports.

---

## 4.2 Analyse des besoins utilisateurs

Les personas identifiés guident les priorités d'interface :

**Persona A — Administrateur NOC :** configure les comptes, consulte l'audit, peut injecter des métriques pour tester l'IA.

**Persona B — Ingénieur réseau :** surveille le dashboard, traite les incidents, utilise la carte pour localiser les sites.

**Persona C — Technicien terrain :** consulte les incidents qui le concernent, commente, utilise la messagerie privée.

Chaque persona accède aux mêmes pages de base, mais certaines actions (résolution, administration) sont restreintes par rôle côté API et masquées côté UI.

---

## 4.3 Conception des interfaces

Principes retenus :

1. **Lisibilité** : fond clair, typographie Inter, contrastes conformes aux bonnes pratiques ;
2. **Hiérarchie visuelle** : KPI en haut, détail en dessous ;
3. **Cohérence** : composants cartes (`.kpi-card`, `.admin-panel`) réutilisés ;
4. **Feedback** : toasts incidents, badge messagerie, bannière alerte critique ;
5. **Non-rechargement** : polling + `mergeById` pour limiter le clignotement.

---

## 4.4 Architecture React

```
dashboard/src/
├── App.js                 # Routes protégées
├── auth/AuthContext.js    # Session JWT
├── components/
│   ├── Sidebar.js
│   ├── ChatWidget.js
│   └── CriticalAlertBanner.js
├── pages/
│   ├── Login.jsx
│   ├── Dashboard.jsx
│   ├── NetworkMap.jsx
│   ├── Antennes.jsx
│   ├── Incidents.jsx
│   ├── Admin.jsx
│   └── Reports.jsx
├── services/apiConfig.js
└── utils/dateTime.js, silentRefresh.js
```

**Tableau 4.1 — Structure des composants React**

| Page | Route | Composants clés |
|------|-------|-----------------|
| Login | /login | Formulaire, démo comptes |
| Dashboard | /dashboard | KPI, Recharts, mini-carte |
| Carte | /map | Leaflet, marqueurs statut |
| Antennes | /antennes | Tableau triable, modales |
| Incidents | /incidents | Liste, résolution, commentaires |
| Admin | /admin | Onglets users, audit, antennes |
| Rapports | /reports | Téléchargements PDF/Excel |

---

## 4.5 Organisation des composants

Le composant `ProtectedRoute` redirige vers `/login` si le token JWT est absent. `AuthContext` persiste le token dans `localStorage` et valide la session via `GET /auth/me` au chargement.

---

## 4.6 Communication avec l'API

`apiConfig.js` centralise `API_BASE_URL` (proxy dev ou URL production) et la fonction `authCfg(token)` ajoutant l'en-tête `Authorization: Bearer …`.

```javascript
export const authCfg = (token) => ({
  headers: { Authorization: `Bearer ${token}` },
});
```

Les erreurs réseau sont gérées localement (messagerie inline, toasts incidents) sans bloquer l'application.

---

## 4.7 Réalisation du Dashboard

Le tableau de bord agrège `GET /dashboard/summary` et `GET /dashboard/history`. Cinq cartes KPI présentent : total antennes, normales, alertes, critiques, incidents ouverts. Un graphique **AreaChart** (Recharts) trace la disponibilité sur 12 heures. Une colonne liste les derniers incidents avec lien vers le détail.

**Figure 4.1 : Tableau de bord NOC**

[Insérer capture : page Dashboard complète]

*Source : Réalisation personnelle.*

**Analyse :** Comme illustré dans la figure 4.1, le tableau de bord offre une vision synthétique immédiate de l'état du réseau. Les KPI colorés (vert, orange, rouge) s'alignent sur la taxonomie métier de l'IA. Le graphique temporel permet de détecter une dégradation progressive de la disponibilité, complémentaire aux alertes ponctuelles. La présence de la cartographie miniature renforce la dimension SIG sans quitter la page d'accueil.

**Figure 4.2 : Indicateurs KPI du dashboard**

[Insérer capture : zoom sur les 5 cartes KPI]

**Analyse :** Chaque KPI est cliquable conceptuellement via la navigation vers les modules détaillés (antennes, incidents). Cette granularité répond au besoin d'escalade rapide décrit au chapitre 1.

**Figure 4.3 : Graphique de disponibilité (12 h)**

[Insérer capture : graphique Recharts]

**Analyse :** L'axe temporel utilise les données renvoyées par l'API agrégées par tranches de 30 minutes. L'affichage en heure Tunisie évite la confusion liée au décalage UTC.

---

## 4.8 Gestion des incidents

La page `Incidents.jsx` charge `GET /incidents` avec rafraîchissement toutes les **10 secondes** et fusion par identifiant (`mergeById`). L'ingénieur peut résoudre un incident (`POST /incidents/:id/resolve`) avec mise à jour optimiste de l'interface.

**Figure 4.4 : Interface de gestion des incidents**

[Insérer capture : liste incidents avec badges statut]

**Analyse :** La figure 4.4 montre la séparation visuelle entre incidents en cours et résolus. Les métadonnées (antenne, zone, criticité, date) proviennent de la jointure SQL côté backend. Le module supporte les commentaires et la modération admin via routes dédiées.

**Figure 4.5 : Détail incident déplié avec métriques**

[Insérer capture : carte incident ouverte]

**Figure 4.6 : Résolution d'incident**

[Insérer capture : bouton résolution / toast succès]

**Analyse :** La résolution déclenche côté serveur la fonction `finalize_incident_resolution` qui remet l'antenne en état normal, clôture les incidents liés et enregistre l'audit. L'opérateur obtient un retour visuel immédiat grâce à l'optimistic update.

---

## 4.9 Gestion des antennes

**Figure 4.7 : Liste des antennes supervisées**

[Insérer capture : tableau antennes avec tri colonnes]

**Analyse :** Le tableau permet le tri par nom, zone, statut, température, CPU, disponibilité. Les filtres par zone et statut réduisent le bruit cognitif sur 121 lignes. L'export CSV s'appuie sur `GET /export/antennes`.

**Figure 4.8 : Fiche / modale antenne**

[Insérer capture : création ou édition]

**Figure 4.9 : Historique antenne**

[Insérer capture : page AntenneHistory]

---

## 4.10 Carte réseau

La page `NetworkMap.jsx` instancie un `MapContainer` Leaflet centré sur Mahdia (35,35°N, 10,85°E). Les tuiles proviennent d'**OpenStreetMap**. Chaque antenne est un marqueur `divIcon` coloré : vert (normal), orange (alerte), rouge pulsant (critique).

**Figure 4.10 : Carte réseau interactive**

[Insérer capture : carte OSM avec marqueurs]

*Source : Réalisation personnelle.*

**Analyse :** Comme illustré dans la figure 4.10, la carte réseau permet la visualisation géographique des antennes supervisées. Les pastilles de filtre à gauche (Sites, Normaux, Alertes, Crit.) agissent sur la couche affichée sans recharger la page. Le pop-up au clic expose température, CPU, disponibilité, score IA et lien vers l'historique — conciliant SIG et données temps réel.

**Figure 4.11 : Pop-up métriques sur la carte**

[Insérer capture : popup Leaflet]

---

## 4.11 Messagerie interne

Le composant `ChatWidget` flottant gère un canal public et des conversations privées (`/chat/private/:id`). Polling 5 s, badge non-lus via `/chat/unread/summary`, marquage lu à l'ouverture.

**Figure 4.12 : Messagerie interne NOC**

[Insérer capture : widget chat ouvert]

**Analyse :** La messagerie répond au besoin de coordination entre ingénieurs et techniciens sans quitter l'outil de supervision. Les horodatages en fuseau Tunisie et les messages d'erreur explicites améliorent l'expérience opérationnelle.

---

## 4.12 Administration

**Figure 4.13 : Gestion des utilisateurs**

[Insérer capture : onglet users Admin]

**Analyse :** L'administrateur crée des comptes (rôle, département, statut). Les mots de passe sont hashés côté serveur ; jamais stockés en clair.

**Figure 4.14 : Modification métriques antenne (admin)**

[Insérer capture : onglet antennes admin + modale métriques]

**Analyse :** L'injection manuelle de métriques via `PUT /antennes/:id/metriques` déclenche le pipeline IA — utile pour la démonstration en soutenance.

---

## 4.13 Journal d'audit

**Figure 4.15 : Journal d'audit — filtres et export CSV**

[Insérer capture : tableau audit]

**Analyse :** Chaque action sensible (connexion, modification antenne, incident, message, export) génère une entrée avec utilisateur, action, cible, valeurs avant/après et adresse IP. Les filtres (utilisateur, date, type) facilitent les enquêtes post-incident.

---

## 4.14 Rapports statistiques

**Figure 4.16 : Module rapports**

[Insérer capture : page Reports]

**Analyse :** Les rapports PDF (quotidien, incidents, IA) et l'export Excel antennes s'adressent au reporting managérial. Les exports CSV complètent l'interopérabilité avec Excel métier.

---

## 4.15 Bannière d'alerte et temps réel

`CriticalAlertBanner` interroge `GET /alerts/critical` toutes les 15 secondes et affiche une bannière rouge si un incident critique est ouvert.

**Figure 4.17 : Bannière d'alerte critique**

[Insérer capture : bannière en haut de l'écran]

**Tableau 4.2 — Intervalles de rafraîchissement automatique**

| Module | Intervalle |
|--------|------------|
| Dashboard | 15 s |
| Carte | 15 s |
| Antennes | 15 s |
| Incidents | 10 s |
| Messagerie | 5 s |
| Admin | 30 s |

Le mécanisme `mergeById` préserve les références React des lignes inchangées pour éviter le clignotement.

---

## 4.16 Responsive design

L'interface cible principalement des postes NOC (écrans 1920×1080). La sidebar est fixe ; les tableaux antennes et incidents défilent horizontalement sur petits écrans. Une adaptation mobile complète constitue une perspective d'amélioration.

---

## 4.17 Tests frontend

- Tests manuels des parcours : login → dashboard → carte → résolution incident ;
- Vérification expiration token (redirection login) ;
- Build production `npm run build` sans erreur ;
- Tests de non-régression visuelle après chaque sprint.

---

## Conclusion du chapitre 4

Le sprint 2 a livré une interface React complète, professionnelle et alignée sur les processus NOC de Mahdia. Les figures 4.1 à 4.17 structurent la démonstration en soutenance : chaque écran correspond à un besoin fonctionnel identifié au chapitre 2. L'intégration API, le rafraîchissement silencieux et la cartographie constituent les apports les plus visibles pour les utilisateurs finaux.

---

*Fin du chapitre 4 — environ 22 pages avec captures.*
