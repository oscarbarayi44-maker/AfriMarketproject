"""Régénère les graphiques avec la charte graphique AfriMarket (vert forêt /
vert vif / blanc), destinés au PowerPoint et au rapport PDF."""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from cycler import cycler

from afrimarket import analysis, branding, pipeline

FIGS = PROJECT_ROOT / "figures_brand"
FIGS.mkdir(exist_ok=True)

plt.rcParams.update({
    "font.family": "Calibri" if "Calibri" in {f.name for f in matplotlib.font_manager.fontManager.ttflist} else "DejaVu Sans",
    "axes.prop_cycle": cycler(color=branding.CATEGORICAL_PALETTE),
    "axes.edgecolor": branding.GREY,
    "axes.labelcolor": branding.TEXT_DARK,
    "text.color": branding.TEXT_DARK,
    "xtick.color": branding.TEXT_DARK,
    "ytick.color": branding.TEXT_DARK,
    "axes.titlecolor": branding.DARK_GREEN,
    "axes.titleweight": "bold",
    "axes.titlesize": 14,
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "axes.grid": True,
    "grid.color": branding.PALE_GREEN,
    "grid.linewidth": 0.8,
    "axes.spines.top": False,
    "axes.spines.right": False,
})

df = pipeline.run_pipeline(save=False)

perf = analysis.performance_globale(df)
cat = analysis.analyse_categorie(df)
geo = analysis.analyse_geographique(df)
mkt = analysis.analyse_marketing(df)
cli = analysis.analyse_clients(df)


def savefig(name):
    plt.tight_layout()
    plt.savefig(FIGS / name, dpi=200, facecolor="white")
    plt.close()


def bar(data, x, y, title, ylabel, fmt_pct=False, figsize=(7, 4.2), rotation=0):
    plt.figure(figsize=figsize)
    bars = plt.bar(data[x], data[y], color=branding.BRAND_GREEN, edgecolor=branding.DARK_GREEN, linewidth=0.6)
    bars[int(data[y].idxmax())].set_color(branding.DARK_GREEN)
    plt.title(title)
    plt.ylabel(ylabel)
    plt.xticks(rotation=rotation)
    if fmt_pct:
        plt.gca().yaxis.set_major_formatter(mticker.PercentFormatter(xmax=1))


# CA par catégorie
bar(cat["synthese"], "categorie", "ca", "Chiffre d'affaires par catégorie", "CA ($)")
savefig("ca_par_categorie.png")

# Taux de retour par catégorie
bar(cat["synthese"], "categorie", "taux_retour", "Taux de retour par catégorie", "Taux de retour", fmt_pct=True)
savefig("taux_retour_categorie.png")

# Évolution mensuelle CA par catégorie
plt.figure(figsize=(8, 4.5))
for i, (categorie, grp) in enumerate(cat["evolution_mensuelle"].groupby("categorie")):
    plt.plot(grp["mois"], grp["chiffre_affaires"], marker="o", label=categorie,
              color=branding.CATEGORICAL_PALETTE[i % len(branding.CATEGORICAL_PALETTE)])
plt.title("Évolution mensuelle du CA par catégorie")
plt.ylabel("CA ($)")
plt.xticks(rotation=30)
plt.legend(frameon=False)
savefig("evolution_ca_categorie.png")

# CA par ville
bar(geo["synthese"], "ville", "ca", "Chiffre d'affaires par ville", "CA ($)", rotation=20)
savefig("ca_par_ville.png")

# Taux d'annulation par ville
plt.figure(figsize=(7, 4.2))
colors = [branding.DARK_GREEN if v == geo["synthese"]["taux_annulation"].max() else branding.BRAND_GREEN
          for v in geo["synthese"]["taux_annulation"]]
plt.bar(geo["synthese"]["ville"], geo["synthese"]["taux_annulation"], color=colors, edgecolor=branding.DARK_GREEN, linewidth=0.6)
plt.title("Taux d'annulation par ville")
plt.ylabel("Taux d'annulation")
plt.gca().yaxis.set_major_formatter(mticker.PercentFormatter(xmax=1))
plt.xticks(rotation=20)
savefig("taux_annulation_ville.png")

# ROI par canal
order = mkt["synthese"].sort_values("roi", ascending=False)
bar(order, "canal_marketing", "roi", "ROI par canal marketing", "ROI", rotation=10)
savefig("roi_par_canal.png")

# Rétention par canal
bar(order, "canal_marketing", "taux_retention", "Taux de rétention par canal", "Taux de rétention", fmt_pct=True, rotation=10)
savefig("retention_par_canal.png")

# Pareto clients
clv_sorted = cli["clv_par_client"].sort_values("valeur_vie_client", ascending=False).reset_index(drop=True)
clv_sorted["rang"] = clv_sorted.index + 1
clv_sorted["part_cumulee_ca"] = clv_sorted["valeur_vie_client"].cumsum() / clv_sorted["valeur_vie_client"].sum()
plt.figure(figsize=(7, 4.5))
plt.plot(clv_sorted["rang"], clv_sorted["part_cumulee_ca"], color=branding.BRAND_GREEN, linewidth=2.5)
plt.axhline(0.8, color=branding.DARK_GREEN, linestyle="--", linewidth=1.2)
plt.title("Courbe de Pareto — part cumulée du CA par client")
plt.xlabel("Nombre de clients (triés par CA décroissant)")
plt.ylabel("Part cumulée du CA")
plt.gca().yaxis.set_major_formatter(mticker.PercentFormatter(xmax=1))
savefig("pareto_clients.png")

# Segmentation clients
plt.figure(figsize=(6, 6))
plt.pie(
    cli["segmentation"]["n_clients"], labels=cli["segmentation"]["segment"], autopct="%1.0f%%",
    colors=branding.CATEGORICAL_PALETTE, wedgeprops={"edgecolor": "white", "linewidth": 1.5},
    textprops={"color": branding.TEXT_DARK},
)
plt.title("Segmentation clients (quartiles de valeur vie client)")
savefig("segmentation_clients.png")

print(f"Figures charte graphique générées dans {FIGS}")
