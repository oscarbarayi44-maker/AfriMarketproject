"""Analyses business AfriMarket : performance globale, catégorie, géographie,
marketing, clients. Toutes les fonctions prennent df_clean (post feature
engineering) et renvoient soit un dict de KPIs, soit un DataFrame prêt à
afficher / tracer.

Conventions retenues (à documenter auprès de la direction) :
- Le chiffre d'affaires et le profit ne sont comptabilisés que sur les
  commandes non annulées (une commande annulée ne génère aucune vente réelle).
- Le taux de retour se calcule sur les commandes effectivement expédiées
  (Livrée + Retournée), une commande annulée n'ayant jamais été livrée.
- Un client "récurrent" est un client ayant passé 2 commandes ou plus.
"""
import numpy as np
import pandas as pd


def _valides(df: pd.DataFrame) -> pd.DataFrame:
    return df[df["statut_commande"] != "Annulée"]


def _expediees(df: pd.DataFrame) -> pd.DataFrame:
    return df[df["statut_commande"].isin(["Livrée", "Retournée"])]


def performance_globale(df: pd.DataFrame) -> dict:
    valides = _valides(df)
    expediees = _expediees(df)
    n_commandes = df["id_commande"].nunique()
    n_annulees = (df["statut_commande"] == "Annulée").sum()
    n_retournees = (df["statut_commande"] == "Retournée").sum()

    return {
        "ca_total": float(valides["chiffre_affaires"].sum()),
        "profit_net_total": float(valides["profit_net"].sum()),
        "panier_moyen": float(valides["chiffre_affaires"].mean()) if len(valides) else 0.0,
        "taux_annulation": float(n_annulees / n_commandes) if n_commandes else 0.0,
        "taux_retour": float(n_retournees / len(expediees)) if len(expediees) else 0.0,
        "n_commandes": int(n_commandes),
    }


def analyse_categorie(df: pd.DataFrame) -> dict:
    valides = _valides(df)
    expediees = _expediees(df)

    par_categorie = valides.groupby("categorie").agg(
        ca=("chiffre_affaires", "sum"),
        marge=("marge_brute", "sum"),
        profit=("profit_net", "sum"),
        n_commandes=("id_commande", "nunique"),
    ).reset_index().sort_values("ca", ascending=False)

    retour = (
        expediees.groupby("categorie")["indicateur_retour"].mean().reset_index()
        .rename(columns={"indicateur_retour": "taux_retour"})
    )
    par_categorie = par_categorie.merge(retour, on="categorie", how="left")

    evolution_mensuelle = (
        valides.groupby(["mois", "categorie"])["chiffre_affaires"].sum().reset_index()
        .sort_values(["mois", "categorie"])
    )

    return {"synthese": par_categorie, "evolution_mensuelle": evolution_mensuelle}


def analyse_geographique(df: pd.DataFrame) -> dict:
    valides = _valides(df)

    par_ville = valides.groupby("ville").agg(
        ca=("chiffre_affaires", "sum"),
        profit=("profit_net", "sum"),
        n_commandes=("id_commande", "nunique"),
    ).reset_index().sort_values("ca", ascending=False)

    annulation_ville = (
        df.groupby("ville")
        .apply(lambda g: (g["statut_commande"] == "Annulée").mean(), include_groups=False)
        .reset_index(name="taux_annulation")
    )
    par_ville = par_ville.merge(annulation_ville, on="ville", how="left")

    ca_mensuel_ville = (
        valides.groupby(["ville", "mois"])["chiffre_affaires"].sum().reset_index()
        .sort_values(["ville", "mois"])
    )
    ca_mensuel_ville["croissance_mensuelle"] = (
        ca_mensuel_ville.groupby("ville")["chiffre_affaires"].pct_change()
    )

    return {"synthese": par_ville, "evolution_mensuelle": ca_mensuel_ville}


def analyse_marketing(df: pd.DataFrame) -> dict:
    valides = _valides(df)

    par_canal = valides.groupby("canal_marketing").agg(
        ca=("chiffre_affaires", "sum"),
        cout_marketing=("cout_marketing", "sum"),
        n_commandes=("id_commande", "nunique"),
        n_clients=("id_client", "nunique"),
    ).reset_index()
    par_canal["roi"] = (par_canal["ca"] - par_canal["cout_marketing"]) / par_canal["cout_marketing"]

    clients_par_canal = valides.groupby(["canal_marketing", "id_client"])["id_commande"].nunique().reset_index()
    retention = (
        clients_par_canal.groupby("canal_marketing")["id_commande"]
        .apply(lambda s: (s >= 2).mean())
        .reset_index(name="taux_retention")
    )
    par_canal = par_canal.merge(retention, on="canal_marketing", how="left")
    par_canal = par_canal.sort_values("roi", ascending=False)

    return {"synthese": par_canal}


def analyse_clients(df: pd.DataFrame) -> dict:
    valides = _valides(df)

    ca_client = valides.groupby("id_client")["chiffre_affaires"].sum().sort_values(ascending=False)
    n_clients = ca_client.shape[0]

    commandes_client = valides.groupby("id_client")["id_commande"].nunique()
    pct_recurrents = float((commandes_client >= 2).mean()) if n_clients else 0.0

    # Pareto 80/20
    cumul = ca_client.cumsum() / ca_client.sum()
    n_clients_80pct_ca = int((cumul <= 0.8).sum()) + 1 if n_clients else 0
    part_clients_80pct_ca = n_clients_80pct_ca / n_clients if n_clients else 0.0

    top10 = ca_client.head(10).reset_index().rename(
        columns={"chiffre_affaires": "ca_total_client"}
    )

    # Segmentation simple par valeur vie client (quartiles)
    clv = valides.groupby("id_client")["chiffre_affaires"].sum().reset_index().rename(
        columns={"chiffre_affaires": "valeur_vie_client"}
    )
    try:
        clv["segment"] = pd.qcut(
            clv["valeur_vie_client"], q=4, labels=["Bronze", "Argent", "Or", "Platine"]
        )
    except ValueError:
        clv["segment"] = "Non segmenté"

    segmentation = clv.groupby("segment", observed=True).agg(
        n_clients=("id_client", "nunique"), ca_total=("valeur_vie_client", "sum")
    ).reset_index()

    return {
        "n_clients_total": int(n_clients),
        "pct_clients_recurrents": pct_recurrents,
        "n_clients_pour_80pct_ca": n_clients_80pct_ca,
        "part_clients_pour_80pct_ca": part_clients_80pct_ca,
        "top10_clients": top10,
        "segmentation": segmentation,
        "clv_par_client": clv,
    }
