import streamlit as st
import pandas as pd
from common_data import ensure_loaded, save_all

FILENAME = "Clients BL.xlsx"

def tab_fichiers():
    st.title("📄 Fichiers")

    # charge (et crée les feuilles manquantes si besoin)
    data = ensure_loaded(FILENAME)

    st.markdown("### Charger un fichier Excel local (remplace sur Drive)")
    up = st.file_uploader("Choisir un fichier .xlsx", type=["xlsx"])
    if up is not None:
        try:
            new_data = pd.read_excel(up, sheet_name=None)
            # simple normalisation : remplacer None par DataFrame vide
            for k,v in list(new_data.items()):
                if v is None:
                    new_data[k] = pd.DataFrame()
            st.session_state["data_xlsx"] = new_data
            save_all(FILENAME)
            st.success("✅ Fichier importé et synchronisé sur Drive.")
            st.rerun()
        except Exception as e:
            st.error(f"❌ Erreur de lecture : {e}")

    st.markdown("### Sauvegarder l'état actuel vers Drive")
    if st.button("💾 Sauvegarder maintenant"):
        save_all(FILENAME)
        st.success("✅ Sauvegarde terminée.")
