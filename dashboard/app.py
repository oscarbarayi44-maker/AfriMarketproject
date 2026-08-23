"""Dashboard interactif AfriMarket (Streamlit).

Lancement :
    streamlit run dashboard/app.py
"""
import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from afrimarket import analysis, branding, pipeline  # noqa: E402

px.defaults.color_discrete_sequence = branding.CATEGORICAL_PALETTE

st.set_page_config(
    page_title="AfriMarket — Dashboard stratégique",
    layout="wide",
    page_icon=str(branding.LOGO_PATH) if branding.LOGO_PATH else "🛒",
)


@st.cache_data
def load_data():
    if not pipeline.CLEAN_PATH.exists():
        pipeline.run_pipeline()
    df = pd.read_csv(pipeline.CLEAN_PATH, parse_dates=["date_commande"])
    return df


df = load_data()

if branding.LOGO_PATH:
    st.sidebar.image(str(branding.LOGO_PATH), use_container_width=True)
else:
    st.sidebar.title("🛒 AfriMarket")
st.sidebar.caption("Filtres du dashboard")

date_min, date_max = df["date_commande"].min(), df["date_commande"].max()
date_range = st.sidebar.date_input(
    "Période", value=(date_min.date(), date_max.date()),
    min_value=date_min.date(), max_value=date_max.date(),
)
villes = st.sidebar.multiselect("Ville", sorted(df["ville"].unique()), default=sorted(df["ville"].unique()))
categories = st.sidebar.multiselect("Catégorie", sorted(df["categorie"].unique()), default=sorted(df["categorie"].unique()))
canaux = st.sidebar.multiselect("Canal marketing", sorted(df["canal_marketing"].unique()), default=sorted(df["canal_marketing"].unique()))

mask = (
    (df["date_commande"].dt.date >= date_range[0])
    & (df["date_commande"].dt.date <= date_range[1])
    & (df["ville"].isin(villes))
    & (df["categorie"].isin(categories))
    & (df["canal_marketing"].isin(canaux))
)
dff = df[mask]

st.title("Dashboard stratégique — AfriMarket")
st.caption(f"{len(dff):,} lignes après filtrage sur {len(df):,} lignes nettoyées au total.".replace(",", " "))

if dff.empty:
    st.warning("Aucune donnée pour ces filtres.")
    st.stop()

perf = analysis.performance_globale(dff)

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("CA total", f"{perf['ca_total']:,.0f} $".replace(",", " "))
c2.metric("Profit net estimé", f"{perf['profit_net_total']:,.0f} $".replace(",", " "))
c3.metric("Panier moyen", f"{perf['panier_moyen']:,.1f} $".replace(",", " "))
c4.metric("Taux d'annulation", f"{perf['taux_annulation']*100:.1f} %")
c5.metric("Taux de retour", f"{perf['taux_retour']*100:.1f} %")

tab_cat, tab_geo, tab_mkt, tab_clients, tab_audit = st.tabs(
    ["📦 Catégories", "🌍 Géographie", "📣 Marketing", "👥 Clients", "🔍 Qualité des données"]
)

with tab_cat:
    res = analysis.analyse_categorie(dff)
    col1, col2 = st.columns(2)
    with col1:
        fig = px.bar(res["synthese"], x="categorie", y="ca", color="categorie", title="CA par catégorie", text_auto=".2s")
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        fig = px.bar(res["synthese"], x="categorie", y="taux_retour", color="categorie", title="Taux de retour par catégorie")
        fig.update_yaxes(tickformat=".0%")
        st.plotly_chart(fig, use_container_width=True)
    fig = px.line(res["evolution_mensuelle"], x="mois", y="chiffre_affaires", color="categorie", markers=True, title="Évolution mensuelle du CA par catégorie")
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(res["synthese"], use_container_width=True)
    st.info("**Question stratégique** : quelle catégorie prioriser/optimiser ? Comparez CA, marge et taux de retour ci-dessus.")

with tab_geo:
    res = analysis.analyse_geographique(dff)
    col1, col2 = st.columns(2)
    with col1:
        fig = px.bar(res["synthese"], x="ville", y="ca", color="ville", title="CA par ville", text_auto=".2s")
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        fig = px.bar(res["synthese"], x="ville", y="taux_annulation", color="ville", title="Taux d'annulation par ville")
        fig.update_yaxes(tickformat=".0%")
        st.plotly_chart(fig, use_container_width=True)
    fig = px.line(res["evolution_mensuelle"], x="mois", y="chiffre_affaires", color="ville", markers=True, title="Évolution mensuelle du CA par ville")
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(res["synthese"], use_container_width=True)
    st.info("**Question stratégique** : où investir davantage ? Repérez les villes à fort CA et faible taux d'annulation.")

with tab_mkt:
    res = analysis.analyse_marketing(dff)
    col1, col2 = st.columns(2)
    with col1:
        fig = px.bar(res["synthese"], x="canal_marketing", y="roi", color="canal_marketing", title="ROI par canal marketing")
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        fig = px.bar(res["synthese"], x="canal_marketing", y="taux_retention", color="canal_marketing", title="Taux de rétention par canal")
        fig.update_yaxes(tickformat=".0%")
        st.plotly_chart(fig, use_container_width=True)
    fig = px.scatter(res["synthese"], x="cout_marketing", y="ca", size="n_commandes", color="canal_marketing", title="Coût marketing vs CA généré par canal")
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(res["synthese"], use_container_width=True)
    st.info("**Question stratégique** : quel canal mérite plus de budget ? Lequel réduire ? Regardez le ROI et la rétention conjointement.")

with tab_clients:
    res = analysis.analyse_clients(dff)
    col1, col2, col3 = st.columns(3)
    col1.metric("Nombre total de clients", res["n_clients_total"])
    col2.metric("% clients récurrents", f"{res['pct_clients_recurrents']*100:.1f} %")
    col3.metric("% clients générant 80% du CA", f"{res['part_clients_pour_80pct_ca']*100:.1f} %")

    col1, col2 = st.columns(2)
    with col1:
        fig = px.bar(res["top10_clients"], x="id_client", y="ca_total_client", title="Top 10 clients par CA")
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        fig = px.pie(res["segmentation"], names="segment", values="n_clients", title="Segmentation clients (quartiles de valeur vie client)")
        st.plotly_chart(fig, use_container_width=True)

    clv_sorted = res["clv_par_client"].sort_values("valeur_vie_client", ascending=False).reset_index(drop=True)
    clv_sorted["rang"] = clv_sorted.index + 1
    clv_sorted["part_cumulee_ca"] = clv_sorted["valeur_vie_client"].cumsum() / clv_sorted["valeur_vie_client"].sum()
    fig = px.line(clv_sorted, x="rang", y="part_cumulee_ca", title="Courbe de Pareto — part cumulée du CA par client")
    fig.add_hline(y=0.8, line_dash="dash", line_color="red")
    fig.update_yaxes(tickformat=".0%")
    st.plotly_chart(fig, use_container_width=True)
    st.info("**Question stratégique** : comment améliorer la rétention ? Ciblez les segments Bronze/Argent avec des offres de fidélisation.")

with tab_audit:
    st.subheader("Qualité des données brutes")
    raw = pipeline.load_raw()
    audit = pipeline.audit_report(raw)
    st.json(audit)
