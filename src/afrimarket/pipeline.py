"""Pipeline de données AfriMarket : chargement, audit, nettoyage, feature engineering.

Hypothèse business documentée : le dataset ne fournit pas de coût d'achat produit.
On retient une marge brute forfaitaire de 35% du chiffre d'affaires (hypothèse
raisonnable pour un e-commerce généraliste multi-catégories), à ajuster si la
direction fournit un coût matière réel par catégorie.
"""
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_PATH = PROJECT_ROOT / "data" / "raw" / "afrimarket_dataset_senior.csv"
CLEAN_PATH = PROJECT_ROOT / "data" / "processed" / "df_clean.csv"

MARGE_BRUTE_HYPOTHESE = 0.35

CANONICAL_CITIES = {
    "kinshassa": "Kinshasa",
    "kinshasa": "Kinshasa",
    "abidjan": "Abidjan",
    "brazzaville": "Brazzaville",
    "cotonou": "Cotonou",
    "dakar": "Dakar",
    "douala": "Douala",
    "libreville": "Libreville",
    "lomé": "Lomé",
    "lome": "Lomé",
}

CANONICAL_CATEGORIES = {
    "electronique": "Électronique",
    "électronique": "Électronique",
    "mode": "Mode",
    "beauté": "Beauté",
    "beaute": "Beauté",
    "maison": "Maison",
}

CANONICAL_STATUS = {
    "livrée": "Livrée",
    "livree": "Livrée",
    "annulée": "Annulée",
    "annulee": "Annulée",
    "retournée": "Retournée",
    "retournee": "Retournée",
}


def load_raw(path: Path = RAW_PATH) -> pd.DataFrame:
    return pd.read_csv(path)


def audit_report(df: pd.DataFrame) -> dict:
    """Diagnostic qualité des données brutes, sans aucune modification."""
    report = {
        "n_lignes": int(len(df)),
        "n_colonnes": int(df.shape[1]),
        "colonnes": list(df.columns),
        "dtypes": {c: str(t) for c, t in df.dtypes.items()},
        "valeurs_manquantes": {c: int(v) for c, v in df.isna().sum().items() if v > 0},
        "doublons_lignes_completes": int(df.duplicated().sum()),
        "doublons_id_commande": int(df.duplicated(subset=["id_commande"]).sum()),
        "remises_negatives": int((df["remise"] < 0).sum()),
        "prix_negatifs": int((df["prix_unitaire"] < 0).sum()),
        "quantites_nulles": int((df["quantite"] == 0).sum()),
        "villes_uniques_brutes": sorted(df["ville"].dropna().unique().tolist()),
        "categories_uniques_brutes": sorted(df["categorie"].dropna().unique().tolist()),
        "statuts_uniques_bruts": sorted(df["statut_commande"].dropna().unique().tolist()),
        "canaux_marketing_uniques": sorted(df["canal_marketing"].dropna().unique().tolist()),
        "methodes_paiement_uniques": sorted(df["methode_paiement"].dropna().unique().tolist()),
    }
    prix = pd.to_numeric(df["prix_unitaire"], errors="coerce")
    q1, q3 = prix.quantile(0.25), prix.quantile(0.75)
    iqr = q3 - q1
    borne_haute = q3 + 1.5 * iqr
    report["prix_outliers_iqr"] = int((prix > borne_haute).sum())
    return report


def _cap_iqr(s: pd.Series) -> pd.Series:
    q1, q3 = s.quantile(0.25), s.quantile(0.75)
    iqr = q3 - q1
    lower, upper = max(q1 - 1.5 * iqr, 0), q3 + 1.5 * iqr
    return s.clip(lower=lower, upper=upper)


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """Retourne df_clean : dataset nettoyé et fiabilisé pour l'analyse."""
    df = df.copy()

    # 1. Dates -> datetime standard
    df["date_commande"] = pd.to_datetime(df["date_commande"], errors="coerce")

    # 2. Doublons : lignes strictement identiques puis id_commande dupliqué
    df = df.drop_duplicates(keep="first")
    df = df.drop_duplicates(subset=["id_commande"], keep="first")

    # 3. Normalisation textuelle (villes, catégories, statuts)
    df["ville"] = (
        df["ville"].astype(str).str.strip().str.lower().map(CANONICAL_CITIES).fillna(df["ville"])
    )
    df["categorie"] = (
        df["categorie"].astype(str).str.strip().str.lower().map(CANONICAL_CATEGORIES).fillna(df["categorie"])
    )
    df["statut_commande"] = (
        df["statut_commande"].astype(str).str.strip().str.lower().map(CANONICAL_STATUS).fillna(df["statut_commande"])
    )

    # 4. Remises négatives : erreur de saisie -> valeur absolue, plafonnée à 90%
    df["remise"] = pd.to_numeric(df["remise"], errors="coerce").fillna(0).abs().clip(0, 0.9)

    # 5. Prix aberrants : négatifs -> manquants puis imputés par la médiane de la
    #    catégorie ; valeurs extrêmes plafonnées par IQR (par catégorie)
    df["prix_unitaire"] = pd.to_numeric(df["prix_unitaire"], errors="coerce")
    df.loc[df["prix_unitaire"] < 0, "prix_unitaire"] = np.nan
    df["prix_unitaire"] = df.groupby("categorie")["prix_unitaire"].transform(
        lambda s: s.fillna(s.median())
    )
    df["prix_unitaire"] = df.groupby("categorie")["prix_unitaire"].transform(_cap_iqr)

    # 6. Quantités nulles : aucune vente réelle -> lignes supprimées
    df["quantite"] = pd.to_numeric(df["quantite"], errors="coerce").fillna(0)
    df = df[df["quantite"] > 0]

    # 7. Coûts : conversion numérique stricte, valeurs manquantes -> 0
    df["cout_marketing"] = pd.to_numeric(df["cout_marketing"], errors="coerce").fillna(0)
    df["cout_livraison"] = pd.to_numeric(df["cout_livraison"], errors="coerce").fillna(0)

    # 8. Lignes non exploitables (date ou prix manquant après nettoyage)
    df = df.dropna(subset=["date_commande", "prix_unitaire"])

    return df.reset_index(drop=True)


def feature_engineering(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df["chiffre_affaires"] = df["prix_unitaire"] * df["quantite"] * (1 - df["remise"])
    df["marge_brute"] = df["chiffre_affaires"] * MARGE_BRUTE_HYPOTHESE
    df["profit_net"] = df["marge_brute"] - df["cout_livraison"] - df["cout_marketing"]
    df["mois"] = df["date_commande"].dt.to_period("M").astype(str)
    df["indicateur_retour"] = (df["statut_commande"] == "Retournée").astype(int)

    commandes_par_client = df.groupby("id_client")["id_commande"].nunique()
    df["nombre_commandes_par_client"] = df["id_client"].map(commandes_par_client)

    clv = df.groupby("id_client")["chiffre_affaires"].sum()
    df["valeur_vie_client"] = df["id_client"].map(clv)

    return df


def run_pipeline(save: bool = True) -> pd.DataFrame:
    raw = load_raw()
    cleaned = clean_data(raw)
    enriched = feature_engineering(cleaned)
    if save:
        CLEAN_PATH.parent.mkdir(parents=True, exist_ok=True)
        enriched.to_csv(CLEAN_PATH, index=False)
    return enriched


if __name__ == "__main__":
    df = run_pipeline()
    print(f"df_clean sauvegardé : {CLEAN_PATH} ({len(df)} lignes)")
