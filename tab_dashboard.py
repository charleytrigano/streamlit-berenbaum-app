import streamlit as st
import pandas as pd
from common_data import ensure_loaded

def tab_dashboard():
    st.header("📊 Dashboard")

    data = ensure_loaded()
    if data is None or "Clients" not in data or data["Clients"].empty:
        st.info("Aucune donnée client à afficher.")
        return

    df = data["Clients"].copy()

    # Nettoyage pour faciliter les KPI
    def to_float(x):
        try:
            return float(str(x).replace(",", ".").replace(" ", ""))
        except:
            return 0.0

    df["Acompte 1"] = df["Acompte 1"].apply(to_float)
    df["Montant honoraires (US $)"] = df["Montant honoraires (US $)"].apply(to_float)

    # Logique ESCROW selon les règles métier
    escrow_checked = df["Escrow"] == True
    escrow_auto = (
        (df["Montant honoraires (US $)"] == 0) &
        (df["Acompte 1"] > 0) &
        ((df["Escrow"] == False) | (df["Escrow"].isna()))
    )
    escrow_mask = escrow_checked | escrow_auto
    escrow_df = df[escrow_mask]

    # KPIs
    total_clients = len(df)
    total_escrow_dossiers = len(escrow_df)
    total_escrow_usd = escrow_df["Acompte 1"].sum()

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total dossiers clients", total_clients)
    with col2:
        st.metric("Nombre de dossiers en escrow", total_escrow_dossiers)
    with col3:
        st.metric("Total Escrow (US $)", f"{total_escrow_usd:,.2f}")

    # (Optionnel) Autres KPI financiers
    total_honoraires = df["Montant honoraires (US $)"].sum()
    total_facture = df[["Montant honoraires (US $)", "Autres frais (US $)"]].apply(to_float).sum().sum() if "Autres frais (US $)" in df.columns else total_honoraires

    col4, col5 = st.columns(2)
    with col4:
        st.metric("Honoraires facturés (US $)", f"{total_honoraires:,.2f}")
    with col5:
        st.metric("Total facturé (Honoraires + frais)", f"{total_facture:,.2f}")

    st.subheader("Dossiers en escrow")
    st.dataframe(
        escrow_df[["Dossier N", "Nom", "Acompte 1", "Escrow"]],
        use_container_width=True
    )

    st.subheader("Liste synthétique des clients")
    st.dataframe(
        df[["Dossier N", "Nom", "Montant honoraires (US $)", "Acompte 1"]],
        use_container_width=True
    )
