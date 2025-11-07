import streamlit as st
import pandas as pd

def main():
    st.header("✏️ / 🗑️ Gestion des dossiers")
    df = st.session_state.get("clients_df")
    if df is None or df.empty:
        st.info("Aucun dossier disponible.")
        return

    st.dataframe(df, use_container_width=True)

    idx = st.number_input("Index à supprimer", min_value=0, max_value=len(df)-1 if len(df)>0 else 0, step=1)
    if st.button("🗑️ Supprimer"):
        df = df.drop(idx).reset_index(drop=True)
        st.session_state["clients_df"] = df
        st.success("Dossier supprimé.")
