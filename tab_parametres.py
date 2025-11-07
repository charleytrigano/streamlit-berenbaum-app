import streamlit as st
import pandas as pd

def main():
    st.header("⚙️ Paramètres")
    st.markdown("Téléchargez ou exportez vos fichiers ici.")

    df = st.session_state.get("clients_df")
    if df is not None and not df.empty:
        st.download_button(
            "💾 Télécharger les clients (Excel)",
            data=df.to_csv(index=False).encode("utf-8"),
            file_name="clients_export.csv",
            mime="text/csv"
        )
    else:
        st.info("Aucune donnée à exporter.")
