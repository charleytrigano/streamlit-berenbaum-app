import streamlit as st
import pandas as pd
import numpy as np
from common_data import ensure_loaded

def tab_escrow():
    st.header("🛡️ Escrow – Suivi des dossiers")

    data = ensure_loaded()
    if data is None or "Clients" not in data or data["Clients"].empty:
        st.info("Aucun fichier chargé.")
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
    if "Escrow" not in df.columns:
        df["Escrow"] = False

    def escrow_bool(val):
        val = str(val).strip().lower()
        return val in ["true", "vrai", "1", "oui", "x", "ok"]

    df["Escrow"] = df["Escrow"].apply(escrow_bool)

    # -- Sélection Escrow principal --
    mask_escrow = df["Escrow"] == True
    mask_zero_honoraires = (df["Montant honoraires (US $)"] == 0)
    mask_acompte_positif = (df["Acompte 1"] > 0)
    mask_auto = mask_zero_honoraires & mask_acompte_positif
    escrow_df = df[mask_escrow | mask_auto].copy()

    if escrow_df.empty:
        st.info("Aucun dossier en Escrow pour le moment.")
        return

    escrow_df["Montant escrow"] = escrow_df["Acompte 1"]

    # -- Statut de déblocage pour suivi opérationnel --
    def statut_debloque(row):
        sent = str(row.get("Dossier envoyé", "")).strip().lower() in ["true", "vrai", "1", "oui", "x", "ok"]
        date_envoi = str(row.get("Date envoi", "")).strip()
        if sent and date_envoi and not pd.isna(date_envoi):
            return "À débloquer"
        else:
            return "Bloqué"
    escrow_df["Statut"] = escrow_df.apply(statut_debloque, axis=1)

    # ---- Tableau principal ---
    st.subheader("📋 Dossiers concernés par Escrow")
    st.dataframe(
        escrow_df[
            [
                "Dossier N",
                "Nom",
                "Montant honoraires (US $)",
                "Acompte 1",
                "Montant escrow",
                "Escrow",
                "Dossier envoyé",
                "Date envoi",
                "Statut"
            ]
        ],
        use_container_width=True
    )

    # --- Tableau Escrow à débloquer + KPIs spécifiques
    escrow_debloquer_df = escrow_df[escrow_df["Statut"] == "À débloquer"].copy()
    montant_total_a_debloquer = escrow_debloquer_df["Montant escrow"].sum()
    nb_a_debloquer = len(escrow_debloquer_df)

    st.subheader("🔓 Escrow à débloquer")
    kpi_col1, kpi_col2 = st.columns(2)
    kpi_col1.metric("Montant total à débloquer (US $)", f"{montant_total_a_debloquer:,.0f}")
    kpi_col2.metric("Nombre de dossiers à débloquer", nb_a_debloquer)

    st.dataframe(
        escrow_debloquer_df[
            [
                "Dossier N",
                "Nom",
                "Acompte 1",
                "Montant escrow",
                "Date envoi",
                "Statut"
            ]
        ],
        use_container_width=True
    )
