# AfriMarket — Analyse stratégique des données commerciales

Analyse de 6 mois d'activité e-commerce d'**AfriMarket**, plateforme panafricaine
opérant dans 4 catégories (Électronique, Mode, Beauté, Maison) sur 8 villes
d'Afrique francophone. Le projet part d'un dataset brut et volontairement
« sale » et livre : un audit qualité, un pipeline de nettoyage, un feature
engineering business, les analyses stratégiques demandées, un dashboard
interactif, un rapport PDF et une présentation PowerPoint — tous générés à
partir du même pipeline Python, donc toujours cohérents entre eux.

## Résultats clés (6 mois)

| CA total | Profit net estimé | Panier moyen | Taux d'annulation | Taux de retour |
|---|---|---|---|---|
| 2,51 M$ | 754 k$ | 272 $ | 1,9 % | 8,3 % |

- **Électronique** porte 74,6 % du CA et 82 % du profit — à prioriser, mais son
  taux de retour (14,1 %) doit être maîtrisé.
- **Mode** et **Beauté** ont une marge quasi entièrement absorbée par les coûts
  logistiques/marketing (57 % et 88 %) — à corriger via le panier moyen.
- **Douala** affiche un taux d'annulation anormal (12,9 % vs < 1 % ailleurs) —
  anomalie opérationnelle à auditer en priorité.
- Le canal **Email** a le meilleur ROI marketing (230) mais est sous-financé ;
  **Influenceur** a le pire ROI et la pire rétention.
- 31,9 % des clients génèrent 80 % du CA ; le segment **Platine** (25 % des
  clients) génère 72 % du CA total.

Le détail, la méthodologie et les 5 recommandations stratégiques sont dans le
[rapport PDF](docs/AfriMarket_Rapport_Strategique.pdf), le
[résumé exécutif Word](docs/Resume_Executif_AfriMarket.docx) et le
[notebook](notebook/Analyse_AfriMarket.ipynb).

## Structure du projet

```
projet AfriMarket/
├── assets/                          Logo de l'entreprise (charte graphique)
├── data/
│   ├── raw/                         Dataset brut (source)
│   └── processed/                   df_clean.csv + résultats d'analyse (CSV)
├── src/afrimarket/
│   ├── pipeline.py                  Chargement, audit, nettoyage, feature engineering
│   ├── analysis.py                  Les 5 analyses business (KPIs, catégorie, géo, marketing, clients)
│   └── branding.py                  Charte graphique (couleurs, police, logo) — source unique de vérité
├── notebook/
│   └── Analyse_AfriMarket.ipynb     Notebook complet, exécuté, commenté
├── dashboard/
│   └── app.py                       Dashboard Streamlit interactif
├── figures/                         Graphiques (palette neutre) pour le notebook
├── figures_brand/                   Graphiques (charte AfriMarket) pour le PDF/PowerPoint
├── docs/
│   ├── AfriMarket_Rapport_Strategique.pdf        Rapport stratégique (14 pages)
│   ├── AfriMarket_Presentation_Direction.pptx    Présentation direction (15 slides)
│   ├── Resume_Executif_AfriMarket.docx           Résumé exécutif (4 pages, éditable)
│   ├── audit_report.json                         Résultats d'audit brut
│   └── resultats_analyses.json                   Résultats de toutes les analyses
├── scripts_run/                     Scripts qui génèrent notebook / figures / rapport / PPT
├── .streamlit/config.toml           Thème Streamlit (couleurs de la marque)
├── requirements.txt                 Dépendances de déploiement (dashboard uniquement)
└── requirements-dev.txt             Dépendances complètes (notebook, rapports, PPT)
```

## Installation

Prérequis : Python 3.12+.

```bash
# Dashboard uniquement (déploiement)
pip install -r requirements.txt

# Tout l'environnement de développement (notebook, PDF, PowerPoint)
pip install -r requirements-dev.txt
```

## Utilisation

### 1. Régénérer les données propres et les analyses

```bash
python src/afrimarket/pipeline.py      # produit data/processed/df_clean.csv
python scripts_run/run_all.py          # audit + analyses + figures/ (palette neutre)
```

### 2. Lancer le dashboard interactif

```bash
streamlit run dashboard/app.py
```

Ouvre `http://localhost:8501`. Filtres disponibles : période, ville, catégorie,
canal marketing. 5 onglets : Catégories, Géographie, Marketing, Clients,
Qualité des données.

### 3. Régénérer le notebook

```bash
python scripts_run/build_notebook.py
jupyter nbconvert --to notebook --execute --inplace notebook/Analyse_AfriMarket.ipynb
```

### 4. Régénérer le rapport PDF et le PowerPoint (avec la charte graphique)

```bash
python scripts_run/build_brand_figures.py   # graphiques aux couleurs de la marque
python scripts_run/build_pdf_report.py      # docs/AfriMarket_Rapport_Strategique.pdf
python scripts_run/build_pptx.py            # docs/AfriMarket_Presentation_Direction.pptx
python scripts_run/build_executive_summary.py  # docs/Resume_Executif_AfriMarket.docx
```

Ces 4 scripts partagent `src/afrimarket/branding.py` et
`docs/resultats_analyses.json` : changer un chiffre ou une couleur de marque à
un seul endroit se propage partout après régénération.

## Déployer le dashboard sur Streamlit Community Cloud

1. Pousser ce dépôt sur GitHub.
2. Sur [share.streamlit.io](https://share.streamlit.io), créer une nouvelle
   app en pointant sur `dashboard/app.py`.
3. Streamlit installe automatiquement `requirements.txt` (à la racine) — pas
   besoin de `requirements-dev.txt` en production, il n'est utile qu'en local
   pour régénérer notebook/rapports/PPT.
4. Le thème (`.streamlit/config.toml`) et le logo (`assets/logo.jpg`) sont
   embarqués dans le dépôt et repris automatiquement.

## Méthodologie (résumé)

- **Audit** : 10 100 commandes brutes, 100 doublons, 614 remises négatives,
  632 prix négatifs, 608 quantités nulles, 799 valeurs de prix extrêmes (IQR),
  incohérences de saisie (villes, catégories, statuts).
- **Nettoyage** → `df_clean` : 9 400 commandes valides, 1 734 clients.
- **Hypothèse business documentée** : en l'absence de coût d'achat produit
  dans les données, la marge brute est estimée à **35 % du chiffre
  d'affaires** (`MARGE_BRUTE_HYPOTHESE` dans `pipeline.py`) — à ajuster si un
  coût matière réel est communiqué par la direction.
- **Conventions de calcul** : le CA et le profit excluent les commandes
  annulées ; le taux de retour se calcule sur les commandes expédiées
  (Livrée + Retournée).

Détail complet dans la section 1 à 3 du [notebook](notebook/Analyse_AfriMarket.ipynb)
et du [rapport PDF](docs/AfriMarket_Rapport_Strategique.pdf).

## Charte graphique

Définie une seule fois dans `src/afrimarket/branding.py`, réutilisée par le
dashboard, le PDF et le PowerPoint :

| Rôle | Couleur |
|---|---|
| Vert foncé (titres, en-têtes) | `#14532D` |
| Vert marque (accent principal) | `#2E8B57` |
| Vert clair (accent secondaire) | `#66BB6A` |
| Vert pâle (fonds de bloc) | `#EAF5EC` |

Le logo est détecté automatiquement dans `assets/` (`branding.find_logo()`) :
pour le changer, il suffit de remplacer le fichier dans ce dossier et de
relancer les scripts de génération.
