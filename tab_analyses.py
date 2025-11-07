import streamlit as st
import pandas as pd

def main():
    st.header("📈 Analyses")

    df = st.session_state.get("clients_df")
    if df is None or df.empty:
        st.warning("Aucune donnée à analyser.")
        return

    st.subheader("Distribution des montants")
    if "Montant" in df.columns:
        st.bar_chart(df["Montant"])
    else:
        st.info("Aucune colonne 'Montant' trouvée.")
