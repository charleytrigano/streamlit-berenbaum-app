import streamlit as st
import pandas as pd
import numpy as np
from common_data import ensure_loaded

def tab_dashboard():
    st.header("📊 Dashboard")

    st.markdown(
        """
        <style>
        .stMetric .number { font-size: 1.2rem !important; }
        </style>
        """,
        unsafe_allow_html=True
    )

    data = ensure_loaded()
    if data is None or "Clients" not in data or data["Clients"].empty:
        st.info("Aucune donnée client à afficher.")
        return

    df = data["Clients"].copy()

    def to_float(x):
        try:
            f = float(str(x).replace(",", ".").replace(" ", ""))
            if (str(x).strip().lower() in ["none", "nan", "", "nonetype"] or pd.isna(x)):
                return 0.0
            return f
        except Exception:
            return 0.0

    df["Montant honoraires (US $)"] = df["Montant honoraires (US $)"].apply(to_float)
    df["Acompte 1"] = df["Acompte 1"].apply(to_float)
    if "Autres frais (US $)" in df.columns:
        df["Autres frais (US $)"] = df["Autres frais (US $)"].apply(to_float)
        total_autres_frais = df["Autres frais (US $)"].sum()
    else:
        total_autres_frais = 0

    if "Escrow" not in df.columns:
        df["Escrow"] = False

    def escrow_bool(val):
        val = str(val).strip().lower()
        return val in ["true", "vrai", "1", "oui", "x", "ok"]

    df["Escrow"] = df["Escrow"].apply(escrow_bool)

    # -- CORRECT LOGIC for Escrow (use UNION of both conditions)
    mask_escrow = df["Escrow"] == True
    mask_zero_honoraires = (df["Montant honoraires (US $)"] == 0)
    mask_acompte_positif = (df["Acompte 1"] > 0)
    mask_auto = mask_zero_honoraires & mask_acompte_positif

    escrow_df = df[mask_escrow | mask_auto].copy()
    escrow_df["Montant escrow"] = escrow_df["Acompte 1"]
    total_escrow_usd = escrow_df["Montant escrow"].sum()
    total_escrow_dossiers = len(escrow_df)

    # -- Autres KPI
    total_clients = len(df)
    total_honoraires = df["Montant honoraires (US $)"].sum()
    total_facture = total_honoraires + total_autres_frais
    total_acomptes = df["Acompte 1"].sum()
    for col in ["Acompte 2", "Acompte 3", "Acompte 4"]:
        if col in df.columns:
            total_acomptes += df[col].apply(to_float).sum()

    # Première ligne KPI (4 colonnes)
    st.subheader("Indicateurs clefs (KPI)")
    kpi_row1 = st.columns(4)
    kpi_row1[0].metric("Nombre total de dossiers clients", int(total_clients))
    kpi_row1[1].metric("Honoraires facturés (US $)", f"{total_honoraires:,.0f}")
    kpi_row1[2].metric("Total autres frais (US $)", f"{total_autres_frais:,.0f}")
    kpi_row1[3].metric("Total facturé (honoraires + frais)", f"{total_facture:,.0f}")

    # Deuxième ligne KPI (4 colonnes)
    kpi_row2 = st.columns(4)
    kpi_row2[0].metric("Total acomptes reçus (US $)", f"{total_acomptes:,.0f}")
    kpi_row2[1].metric("Dossiers en Escrow", total_escrow_dossiers)
    kpi_row2[2].metric("Montant total Escrow (US $)", f"{total_escrow_usd:,.0f}")
    kpi_row2[3].metric("Acomptes Escrow (US $)", f"{total_escrow_usd:,.0f}")

    st.subheader("Dossiers en escrow")
    if not escrow_df.empty:
        st.dataframe(
            escrow_df[
                ["Dossier N", "Nom", "Acompte 1", "Montant escrow", "Escrow"]
            ],
            use_container_width=True
        )
    else:
        st.info("Aucun dossier en Escrow.")

    st.subheader("Liste synthétique des clients")
    columns_to_show = ["Dossier N", "Nom", "Montant honoraires (US $)", "Acompte 1"]
    available_columns = [col for col in columns_to_show if col in df.columns]
    st.dataframe(
        df[available_columns],
        use_container_width=True
    )
