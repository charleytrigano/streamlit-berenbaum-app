import streamlit as st
import pandas as pd
from common_data import ensure_loaded, save_all, MAIN_FILE  # vérifie que ce fichier existe
import os

# Utilitaire pour charger une seule fois le fichier xlsx
def get_client_data():
    if "data_xlsx" not in st.session_state:
        data = ensure_loaded()
        st.session_state["data_xlsx"] = data
    return st.session_state.get("data_xlsx")

def tab_gestion():
    st.header("✏️ / 🗑️ Gestion d’un dossier")

    # Utilise le xlsx déjà chargé
    data = get_client_data()
    if data is None or "Clients" not in data or data["Clients"].empty:
        st.warning("Aucun fichier ou dossier valide.")
        return
    df = data["Clients"]

    # ... Suite inchangée ...
    # À la fin, lors d'une modification
    if st.button("💾 Enregistrer les modifications"):
        try:
            # ... Met à jour les champs de df ...
            data["Clients"] = df          # Mets à jour DataFrame
            st.session_state["data_xlsx"] = data  # Mets à jour la variable session

            save_all()  # Sauvegarde dans le fichier

            st.success("✅ Modifications enregistrées.")
            st.rerun()
        except Exception as e:
            st.error(f"❌ Erreur : {e}")
