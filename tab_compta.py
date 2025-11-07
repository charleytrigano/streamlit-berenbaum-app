import streamlit as st
import pandas as pd

def main():
    st.header("💳 Comptabilité Client")

    df = st.session_state.get("clients_df")
    if df is None or df.empty:
        st.info("Aucun client disponible.")
        return

    st.dataframe(df[["Nom", "Montant"]] if "Nom" in df.columns else df)
