import streamlit as st
from common_data import load_xlsx, save_all, MAIN_FILE

def tab_fichiers():
    st.header("📄 Gestion des fichiers")

    # --- IMPORT FICHIER ---
    uploaded = st.file_uploader("Importer un fichier Excel (.xlsx)", type="xlsx")

    if uploaded:
        file_bytes = uploaded.getvalue()
        data = load_xlsx(file_bytes)

        if data is not None:
            st.session_state["data_xlsx"] = data
            st.success("✅ Fichier chargé avec succès et disponible dans l’application.")

    # --- SI PAS DE FICHIER ---
    if "data_xlsx" not in st.session_state:
        st.info("Aucun fichier chargé pour le moment.")
        return

    data = st.session_state["data_xlsx"]

    # Liste des feuilles détectées
    st.subheader("📑 Feuilles détectées")
    sheet_names = list(data.keys())
    st.write(", ".join(sheet_names))

    # Aperçu
    selected_sheet = st.selectbox("Afficher une feuille", sheet_names)

    df = data[selected_sheet]
    st.dataframe(df, use_container_width=True)

    # --- SAUVEGARDE ---
    st.subheader("💾 Sauvegarde du fichier")

    if st.button("Sauvegarder localement"):
        if save_all():
            st.success("Fichier sauvegardé dans la session.")
            st.download_button(
                "⬇️ Télécharger le fichier sauvegardé",
                data=st.session_state["last_saved_file"],
                file_name=MAIN_FILE,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
