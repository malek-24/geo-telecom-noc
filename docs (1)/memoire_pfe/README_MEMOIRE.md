# Mémoire PFE — GEO-TÉLÉCOM NOC Mahdia

**Auteurs :** Malek Maadi & Abir Said  
**Organisme :** Tunisie Télécom — Centre Technique de Mahdia  
**Année :** 2025–2026  

## Contenu du dossier

| Fichier | Section | Pages indicatives |
|---------|---------|-------------------|
| `00_PAGES_PRELIMINAIRES.md` | Couverture, résumé, sommaire, listes | ~12 |
| `01_INTRODUCTION_GENERALE.md` | Introduction | ~10 |
| `02_CHAPITRE1_CADRE_GENERAL.md` | Chapitre 1 | ~12 |
| `03_CHAPITRE2_PREPARATION.md` | Chapitre 2 | ~14 |
| `04_CHAPITRE3_BACKEND.md` | Chapitre 3 | ~14 |
| `05_CHAPITRE4_FRONTEND.md` | Chapitre 4 (+ figures) | ~22 |
| `06_CHAPITRE5_IA.md` | Chapitre 5 | ~18 |
| `07_CHAPITRE6_IOT_SIMULATION.md` | Chapitre 6 | ~10 |
| `08_CONCLUSION_ANNEXES_BIBLIO.md` | Conclusion, annexes, biblio | ~12 |

**Total estimé : 80 à 100 pages** après insertion des captures et mise en forme Word/LaTeX.

## Compilation en PDF

### Option 1 — Pandoc (recommandé)

```bash
cd "docs (1)/memoire_pfe"
pandoc 00_PAGES_PRELIMINAIRES.md 01_INTRODUCTION_GENERALE.md 02_CHAPITRE1_CADRE_GENERAL.md 03_CHAPITRE2_PREPARATION.md 04_CHAPITRE3_BACKEND.md 05_CHAPITRE4_FRONTEND.md 06_CHAPITRE5_IA.md 07_CHAPITRE6_IOT_SIMULATION.md 08_CONCLUSION_ANNEXES_BIBLIO.md -o MEMOIRE_PFE_COMPLET.pdf --toc --number-sections -V lang=fr -V geometry:margin=2.5cm
```

### Option 2 — Microsoft Word

1. Copier chaque fichier dans l'ordre dans un document unique.  
2. Police **Times New Roman 12**, interligne **1,5**.  
3. Remplacer chaque `[Insérer capture]` par la capture d'écran correspondante.  
4. Générer la table des matières automatique.  
5. Numéroter les figures (Figure X.Y).

## Captures à insérer

Prendre les captures depuis l'application (`http://localhost:3000`) :

- Login, Dashboard, KPI, Graphique 12h  
- Carte réseau, popup antenne  
- Liste antennes, historique  
- Incidents (liste, détail, résolution)  
- Admin (users, audit, métriques)  
- Messagerie, Rapports  
- Carte avec sites alerte/critique (test IA)  
- pgAdmin ou logs simulation  

## Alignement avec le code réel

| Énoncé mémoire | Projet réel |
|----------------|-------------|
| React + JS | `dashboard/` — React 18, **JavaScript** (pas TypeScript) |
| Styles | CSS modules / fichiers `.css` (pas Tailwind) |
| 121 antennes | Bootstrap `prediction.py` |
| Isolation Forest | `api/ia/model.py` |
| Docker | `docker-compose.yml` (ports 3000, 7000, 6000) |

## Personnalisation avant soutenance

- Remplacer `[Nom de l'encadrant académique]` et `[Nom de l'encadrant Tunisie Télécom]`  
- Ajouter logo Tunisie Télécom sur la page de garde  
- Vérifier numérotation des figures après insertion des images  
