import streamlit as st
import pandas as pd

def main():
    st.header("📊 Tableau de bord")

    df = st.session_state.get("clients_df")
    if df is None or df.empty:
        st.warning("Aucune donnée disponible. Chargez un fichier dans l’onglet Fichiers.")
        return

    st.metric("Nombre total de clients", len(df))
    st.metric("Montant total facturé", f"{df['Montant'].sum():,.2f} €" if 'Montant' in df else "N/A")
    st.dataframe(df.head(10))
