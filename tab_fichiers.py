import streamlit as st
import pandas as pd
import escrow_manager as esc

def main():
    st.header("📄 Fichiers")
    st.markdown("Chargez votre fichier Excel principal (Clients BL.xlsx).")

    uploaded = st.file_uploader("Choisir un fichier Excel", type=["xlsx"])
    if uploaded:
        df = pd.read_excel(uploaded)
        st.session_state["clients_df"] = df
        st.success(f"{len(df)} lignes chargées avec succès.")
        st.dataframe(df, use_container_width=True)
    elif "clients_df" in st.session_state:
        st.dataframe(st.session_state["clients_df"], use_container_width=True)
    else:
        st.info("Aucun fichier chargé pour le moment.")
