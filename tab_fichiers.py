import streamlit as st
import pandas as pd
from common_data import ensure_loaded, save_all, MAIN_FILE

def tab_fichiers():
    st.title("📄 Fichiers")

    data = ensure_loaded(MAIN_FILE)

    st.markdown("### Charger un fichier Excel (remplace sur Drive)")
    up = st.file_uploader("Choisir un fichier .xlsx", type=["xlsx"])

    if up:
        try:
            new_data = pd.read_excel(up, sheet_name=None)
            st.session_state["data_xlsx"] = new_data
            save_all(new_data, MAIN_FILE)
            st.success("✅ Fichier importé et synchronisé sur Drive.")
            st.rerun()
        except Exception as e:
            st.error(f"❌ Erreur : {e}")

    st.markdown("### Sauvegarder l'état actuel vers Drive")
    if st.button("💾 Sauvegarder maintenant"):
        save_all(st.session_state.get("data_xlsx"), MAIN_FILE)
        st.success("💾 Sauvegarde terminée.")
