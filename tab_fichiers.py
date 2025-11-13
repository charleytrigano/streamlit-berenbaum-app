import streamlit as st
import pandas as pd
from common_data import load_xlsx, save_all_local, MAIN_FILE

def tab_fichiers():
    st.header("📄 Gestion des fichiers")

    # =============================
    # 1. UPLOAD DU FICHIER
    # =============================
    uploaded_file = st.file_uploader(
        "Importer un fichier Excel (.xlsx)",
        type=["xlsx"],
        key="file_upload"
    )

    if uploaded_file:
        file_bytes = uploaded_file.read()
        data = load_xlsx(file_bytes)

        if data:
            st.session_state["data_xlsx"] = data
            st.success(f"✅ Fichier **{uploaded_file.name}** chargé avec succès !")

            if st.button("💾 Sauvegarder localement (mémoire)"):
                ok = save_all_local(st.session_state["data_xlsx"])
                if ok:
                    st.success("✨ Sauvegarde locale effectuée.")

    st.markdown("---")

    # =============================
    # 2. AFFICHAGE DES FEUILLES
    # =============================
    st.subheader("📑 Feuilles détectées")

    if "data_xlsx" not in st.session_state:
        st.info("Aucun fichier chargé pour le moment.")
        return

    data = st.session_state["data_xlsx"]
    sheet_names = list(data.keys())

    st.write("Feuilles disponibles :", ", ".join(sheet_names))

    # Aperçu rapide
    selected_sheet = st.selectbox("Afficher une feuille :", sheet_names)

    df = data[selected_sheet]

    st.write(f"### Aperçu de **{selected_sheet}**")
    st.dataframe(df)

    st.markdown("---")

    # =============================
    # 3. EXPORT DU FICHIER EN LOCAL
    # =============================
    if "last_saved_file" in st.session_state:
        st.download_button(
            label="⬇️ Télécharger la dernière sauvegarde",
            data=st.session_state["last_saved_file"],
            file_name=MAIN_FILE,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )