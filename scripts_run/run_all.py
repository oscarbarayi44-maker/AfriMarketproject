"""Exécute audit + pipeline + toutes les analyses, sauvegarde résultats en JSON/CSV
et génère les figures (PNG) pour le résumé exécutif."""
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from afrimarket import analysis, pipeline

sns.set_theme(style="whitegrid")

DOCS = PROJECT_ROOT / "docs"
FIGS = PROJECT_ROOT / "figures"
PROC = PROJECT_ROOT / "data" / "processed"
DOCS.mkdir(exist_ok=True)
FIGS.mkdir(exist_ok=True)
PROC.mkdir(parents=True, exist_ok=True)


def to_jsonable(obj):
    if isinstance(obj, pd.DataFrame):
        return obj.to_dict(orient="records")
    if isinstance(obj, dict):
        return {k: to_jsonable(v) for k, v in obj.items()}
    return obj


# --- 1. Audit ---
raw = pipeline.load_raw()
audit = pipeline.audit_report(raw)
(DOCS / "audit_report.json").write_text(json.dumps(audit, indent=2, ensure_ascii=False), encoding="utf-8")
print("Audit sauvegardé.")

# --- 2 & 3. Cleaning + Feature engineering ---
df = pipeline.run_pipeline()
print(f"df_clean : {len(df)} lignes, {df['id_client'].nunique()} clients, {df['id_commande'].nunique()} commandes")

# --- 4. Analyses ---
perf = analysis.performance_globale(df)
cat = analysis.analyse_categorie(df)
geo = analysis.analyse_geographique(df)
mkt = analysis.analyse_marketing(df)
cli = analysis.analyse_clients(df)

results = {
    "performance_globale": perf,
    "analyse_categorie": cat["synthese"],
    "analyse_geographique": geo["synthese"],
    "analyse_marketing": mkt["synthese"],
    "analyse_clients": {
        "n_clients_total": cli["n_clients_total"],
        "pct_clients_recurrents": cli["pct_clients_recurrents"],
        "n_clients_pour_80pct_ca": cli["n_clients_pour_80pct_ca"],
        "part_clients_pour_80pct_ca": cli["part_clients_pour_80pct_ca"],
        "top10_clients": cli["top10_clients"],
        "segmentation": cli["segmentation"],
    },
}
(DOCS / "resultats_analyses.json").write_text(
    json.dumps(to_jsonable(results), indent=2, ensure_ascii=False, default=str), encoding="utf-8"
)
cat["synthese"].to_csv(PROC / "analyse_categorie.csv", index=False)
geo["synthese"].to_csv(PROC / "analyse_geographique.csv", index=False)
mkt["synthese"].to_csv(PROC / "analyse_marketing.csv", index=False)
cli["top10_clients"].to_csv(PROC / "top10_clients.csv", index=False)
cli["segmentation"].to_csv(PROC / "segmentation_clients.csv", index=False)
print("Résultats d'analyse sauvegardés.")

# --- 5. Figures (matplotlib/seaborn, statiques pour le résumé exécutif) ---

def savefig(name):
    plt.tight_layout()
    plt.savefig(FIGS / name, dpi=150)
    plt.close()


# CA par catégorie
plt.figure(figsize=(7, 4))
sns.barplot(data=cat["synthese"], x="categorie", y="ca", hue="categorie", legend=False)
plt.title("Chiffre d'affaires par catégorie")
plt.ylabel("CA ($)")
plt.xlabel("")
savefig("ca_par_categorie.png")

# Taux de retour par catégorie
plt.figure(figsize=(7, 4))
sns.barplot(data=cat["synthese"], x="categorie", y="taux_retour", hue="categorie", legend=False)
plt.title("Taux de retour par catégorie")
plt.ylabel("Taux de retour")
plt.xlabel("")
savefig("taux_retour_categorie.png")

# Évolution mensuelle CA par catégorie
plt.figure(figsize=(8, 4.5))
sns.lineplot(data=cat["evolution_mensuelle"], x="mois", y="chiffre_affaires", hue="categorie", marker="o")
plt.title("Évolution mensuelle du CA par catégorie")
plt.ylabel("CA ($)")
plt.xlabel("Mois")
plt.xticks(rotation=30)
savefig("evolution_ca_categorie.png")

# CA par ville
plt.figure(figsize=(7, 4))
sns.barplot(data=geo["synthese"], x="ville", y="ca", hue="ville", legend=False)
plt.title("Chiffre d'affaires par ville")
plt.ylabel("CA ($)")
plt.xlabel("")
plt.xticks(rotation=20)
savefig("ca_par_ville.png")

# Taux d'annulation par ville
plt.figure(figsize=(7, 4))
sns.barplot(data=geo["synthese"], x="ville", y="taux_annulation", hue="ville", legend=False)
plt.title("Taux d'annulation par ville")
plt.ylabel("Taux d'annulation")
plt.xlabel("")
plt.xticks(rotation=20)
savefig("taux_annulation_ville.png")

# ROI par canal marketing
plt.figure(figsize=(7, 4))
order = mkt["synthese"].sort_values("roi", ascending=False)
sns.barplot(data=order, x="canal_marketing", y="roi", hue="canal_marketing", legend=False)
plt.title("ROI marketing par canal")
plt.ylabel("ROI")
plt.xlabel("")
plt.xticks(rotation=15)
savefig("roi_par_canal.png")

# Rétention par canal
plt.figure(figsize=(7, 4))
sns.barplot(data=order, x="canal_marketing", y="taux_retention", hue="canal_marketing", legend=False)
plt.title("Taux de rétention client par canal")
plt.ylabel("Taux de rétention")
plt.xlabel("")
plt.xticks(rotation=15)
savefig("retention_par_canal.png")

# Pareto clients
clv_sorted = cli["clv_par_client"].sort_values("valeur_vie_client", ascending=False).reset_index(drop=True)
clv_sorted["rang"] = clv_sorted.index + 1
clv_sorted["part_cumulee_ca"] = clv_sorted["valeur_vie_client"].cumsum() / clv_sorted["valeur_vie_client"].sum()
plt.figure(figsize=(7, 4.5))
plt.plot(clv_sorted["rang"], clv_sorted["part_cumulee_ca"])
plt.axhline(0.8, color="red", linestyle="--")
plt.title("Courbe de Pareto — part cumulée du CA par client")
plt.xlabel("Nombre de clients (triés par CA décroissant)")
plt.ylabel("Part cumulée du CA")
savefig("pareto_clients.png")

# Segmentation clients
plt.figure(figsize=(6, 6))
plt.pie(cli["segmentation"]["n_clients"], labels=cli["segmentation"]["segment"], autopct="%1.0f%%")
plt.title("Segmentation clients (quartiles de valeur vie client)")
savefig("segmentation_clients.png")

print("Figures générées dans /figures.")
print("TERMINÉ")
