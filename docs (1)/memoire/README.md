## Mémoire PFE — génération PDF

Ce dossier contient la version **Markdown structurée** du mémoire de PFE (Licence Informatique, Tunisie Télécom — Centre Technique Mahdia).

### Structure

- `00_page_de_garde.md`
- `01_dedicace_remerciements.md`
- `02_resume_abstract.md`
- `03_sommaire_listes.md`
- `10_introduction_generale.md`
- `20_chapitre1_organisation_contexte.md`
- `30_chapitre2_analyse_besoins_uml_scrum.md`
- `40_chapitre3_sprint1_backend_bd_sig_docker.md`
- `50_chapitre4_sprint2_frontend_react_sig_uiux.md` (**chapitre très détaillé**)
- `60_chapitre5_sprint3_intelligence_artificielle.md` (**chapitre très détaillé**)
- `70_chapitre6_sprint4_simulation_iot_temps_reel.md`
- `80_conclusion_generale_perspectives.md`
- `90_bibliographie_webographie.md`
- `99_annexes.md`
- `memoire_pfe_master.md` (fichier maître : concaténation logique)

### Générer un PDF (recommandé : Pandoc + LaTeX)

Pré-requis (Windows) :
- Installer **Pandoc**
- Installer **MiKTeX** ou **TeX Live**

Commande (PowerShell) depuis la racine du projet :

```bash
pandoc "docs (1)/memoire/memoire_pfe_master.md" -o "docs (1)/memoire/Memoire_PFE_TT_Mahdia.pdf" --toc --number-sections --pdf-engine=xelatex -V documentclassoption=12pt -H "docs (1)/memoire/pandoc/preamble.tex"
```

Notes :
- Les **captures d’écran** sont indiquées sous forme d’emplacements `[Insérer Capture]`. Pour un rendu final, ajouter les images (PNG/JPG) dans un sous-dossier `docs (1)/memoire/figures/` puis remplacer l’emplacement par `![](figures/nom.png)`.
- Les diagrammes UML sont fournis en **Mermaid** (compatible GitHub). Pour Pandoc PDF, vous pouvez :
  - soit exporter les diagrammes Mermaid en images (PNG/SVG) et les inclure,
  - soit utiliser un filtre Mermaid (selon votre environnement).

