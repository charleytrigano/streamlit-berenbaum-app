# tab_fichiers.py
import streamlit as st
import pandas as pd
from common_data import ensure_loaded, load_xlsx, MAIN_FILE, save_all_local


def tab_fichiers():
    st.header("📄 Fichiers")

    # Charger les données existantes (depuis session ou fichier du repo)
    data = ensure_loaded(MAIN_FILE)

    st.markdown(f"**Fichier principal actuel :** `{MAIN_FILE}`")

    st.markdown("---")
    st.subheader("📥 Importer un fichier Excel")

    uploaded = st.file_uploader(
        "Choisis un fichier Excel (.xlsx) à utiliser pour cette session",
        type=["xlsx"],
        key="file_uploader_main",
    )

    if uploaded is not None:
        try:
            xls = pd.ExcelFile(uploaded)
            new_data = {sheet: pd.read_excel(xls, sheet_name=sheet) for sheet in xls.sheet_names}
            st.session_state["data_xlsx"] = new_data
            data = new_data
            st.success("✅ Fichier chargé en mémoire pour cette session.")
        except Exception as e:
            st.error(f"❌ Erreur de lecture du fichier : {e}")

    # Aperçu des feuilles
    if not data:
        st.warning("⚠️ Aucune donnée chargée. Charge un fichier Excel ci-dessus.")
        return

    sheets = list(data.keys())
    st.markdown("**Feuilles détectées dans le fichier :** " + ", ".join(f"`{s}`" for s in sheets))

    # Aperçu rapide de la feuille Clients si présente
    if "Clients" in data:
        st.markdown("### 👀 Aperçu de la feuille `Clients`")
        st.dataframe(data["Clients"].head(20), use_container_width=True)
    else:
        st.warning("⚠️ La feuille `Clients` n'existe pas dans ce fichier.")

    # Bouton de sauvegarde locale (dans le conteneur)
    st.markdown("---")
    if st.button("💾 Sauvegarder l'état actuel dans le fichier local", use_container_width=True):
        save_all_local(MAIN_FILE)
