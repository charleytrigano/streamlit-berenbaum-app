import streamlit as st
import pandas as pd
import escrow_manager as esc

def main():
    st.header("🛡️ Escrow")

    try:
        df_escrow = esc.load_escrow()
        if df_escrow.empty:
            st.info("Aucun dossier Escrow à afficher.")
        else:
            st.dataframe(df_escrow, use_container_width=True)
    except Exception as e:
        st.error(f"Erreur lors du chargement Escrow : {e}")
