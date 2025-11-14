import streamlit as st
import pandas as pd
from common_data import ensure_loaded, MAIN_FILE


def tab_escrow():

    st.header("🛡️ Dossiers en Escrow")

    data = ensure_loaded(MAIN_FILE)
    if data is None:
        st.warning("Aucun fichier chargé.")
        return

    df = data["Clients"].copy()

    # ------------ Normalisation colonnes numériques ------------
    def to_float(x):
        try:
            return float(str(x).replace(",", ".").strip())
        except:
            return 0.0

    df["Montant honoraires (US $)"] = df["Montant honoraires (US $)"].map(to_float)
    df["Acompte 1"] = df["Acompte 1"].map(to_float)

    # ------------ Normalisation Escrow ------------
    def to_bool(x):
        x = str(x).strip().lower()
        return x in ["1", "true", "oui", "yes", "y"]
    
    df["Escrow"] = df["Escrow"].map(to_bool)

    # ------------ Règles Escrow ------------
    condition = (
        (df["Escrow"] == True) |
        ((df["Acompte 1"] > 0) & (df["Montant honoraires (US $)"] == 0))
    )

    df_escrow = df[condition]

    if df_escrow.empty:
        st.info("Aucun dossier en Escrow pour le moment.")
        return

    st.subheader("📋 Liste des dossiers en Escrow")
    st.dataframe(df_escrow, use_container_width=True)
