import streamlit as st
from common_data import load_xlsx, save_all_local, MAIN_FILE


def tab_fichiers():
    st.header("📄 Gestion des fichiers")

    # Initialiser session_state si manquant
    if "data_xlsx" not in st.session_state:
        st.session_state["data_xlsx"] = None

    uploaded = st.file_uploader("Importer un fichier Excel (.xlsx)", type=["xlsx"])

    if uploaded:
        file_bytes = uploaded.read()
        data = load_xlsx(file_bytes)

        if data is None:
            st.error("❌ Erreur lors de la lecture du fichier.")
            return

        st.session_state["data_xlsx"] = data
        st.success("✅ Fichier chargé avec succès !")

        # Sauvegarde locale immédiate (en mémoire)
        save_all_local(data)

    # Si aucun fichier n’est encore chargé
    if st.session_state["data_xlsx"] is None:
        st.warning("⚠️ Aucun fichier chargé. Veuillez importer un XLSX.")
        return

    # Récupération des données
    data = st.session_state["data_xlsx"]

    # Sécurité : vérifier bien que c'est un dict
    if not isinstance(data, dict):
        st.error("❌ Données corrompues en mémoire. Veuillez réimporter le fichier.")
        st.session_state["data_xlsx"] = None
        return

    # Affichage des feuilles détectées
    sheet_names = list(data.keys())
    st.write("📑 **Feuilles disponibles :**", ", ".join(sheet_names))

    # Aperçu des feuilles
    selected = st.selectbox("Afficher une feuille :", sheet_names)

    df_preview = data[selected]

    st.subheader(f"Aperçu : {selected}")
    st.dataframe(df_preview)

    # Bouton de sauvegarde (simple)
    if st.button("💾 Sauvegarder localement"):
        if save_all_local(st.session_state["data_xlsx"]):
            st.success("✔️ Sauvegarde locale effectuée !")