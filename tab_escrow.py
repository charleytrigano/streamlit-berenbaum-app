import streamlit as st
import pandas as pd
from common_data import ensure_loaded, save_all, MAIN_FILE

def tab_escrow():

    st.header("💼 Dossiers en Escrow")

    data = ensure_loaded(MAIN_FILE)
    df = data["Clients"].copy()

    # Convertit proprement les nombres
    def to_float(x):
        try:
            return float(str(x).replace(",", ".").strip())
        except:
            return 0.0

    df["Montant honoraires (US $)"] = df["Montant honoraires (US $)"].map(to_float)
    df["Acompte 1"] = df["Acompte 1"].map(to_float)

    # Règles Escrow
    condition_escrow = (
        (df["Escrow"] == 1) |
        ((df["Acompte 1"] > 0) & (df["Montant honoraires (US $)"] == 0))
    )

    df_escrow = df[condition_escrow]

    if df_escrow.empty:
        st.info("Aucun dossier en Escrow pour le moment.")
        return

    st.dataframe(df_escrow, use_container_width=True)
