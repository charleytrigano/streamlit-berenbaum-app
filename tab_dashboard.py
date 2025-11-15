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
    df["Acompte 2"] = df["Acompte 2"].apply(to_float) if "Acompte 2" in df.columns else 0
    df["Acompte 3"] = df["Acompte 3"].apply(to_float) if "Acompte 3" in df.columns else 0
    df["Acompte 4"] = df["Acompte 4"].apply(to_float) if "Acompte 4" in df.columns else 0
    df["Montant honoraires (US $)"] = df["Montant honoraires (US $)"].apply(to_float)
    df["Autres frais (US $)"] = df["Autres frais (US $)"].apply(to_float) if "Autres frais (US $)" in df.columns else 0

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
    total_honoraires = df["Montant honoraires (US $)"].sum()
    total_autres_frais = df["Autres frais (US $)"].sum() if "Autres frais (US $)" in df.columns else 0
    total_facture = total_honoraires + total_autres_frais

    total_acomptes = df["Acompte 1"].sum()
    if "Acompte 2" in df.columns: total_acomptes += df["Acompte 2"].sum()
    if "Acompte 3" in df.columns: total_acomptes += df["Acompte 3"].sum()
    if "Acompte 4" in df.columns: total_acomptes += df["Acompte 4"].sum()

    # Affichage KPI en ligne
    st.subheader("Indicateurs clefs (KPI)")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Nombre total de dossiers clients", total_clients)
    with col2:
        st.metric("Honoraires facturés (US $)", f"{total_honoraires:,.2f}")
    with col3:
        st.metric("Total autres frais (US $)", f"{total_autres_frais:,.2f}")

    col4, col5, col6 = st.columns(3)
    with col4:
        st.metric("Total facturé (honoraires + frais)", f"{total_facture:,.2f}")
    with col5:
        st.metric("Total acomptes reçus (US $)", f"{total_acomptes:,.2f}")
    with col6:
        st.metric("Dossiers en Escrow", total_escrow_dossiers)

    col7, col8 = st.columns(2)
    with col7:
        st.metric("Montant total Escrow (US $)", f"{total_escrow_usd:,.2f}")
    with col8:
        st.metric("Acomptes Escrow (US $)", f"{total_escrow_usd:,.2f}")

    # Tableau dossiers en Escrow
    st.subheader("Dossiers en escrow")
    if not escrow_df.empty:
        st.dataframe(
            escrow_df[["Dossier N", "Nom", "Acompte 1", "Escrow"]],
            use_container_width=True
        )
    else:
        st.info("Aucun dossier en Escrow.")

    # Liste synthétique des clients
    st.subheader("Liste synthétique des clients")
    st.dataframe(
        df[["Dossier N", "Nom", "Montant honoraires (US $)", "Acompte 1"]],
        use_container_width=True
    )
