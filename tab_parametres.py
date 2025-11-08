import streamlit as st
import pandas as pd
import io

EXCEL_FILE = "Clients BL.xlsx"

def tab_parametres():
    """Onglet de configuration : chargement + export Excel."""
    st.header("⚙️ Paramètres de l’application")

    # Charger les données actuelles
    if "data_xlsx" not in st.session_state:
        st.session_state["data_xlsx"] = {}

    data = st.session_state["data_xlsx"]

    st.subheader("📂 Charger le fichier Excel principal")

    uploaded_file = st.file_uploader("Sélectionnez le fichier Excel (Clients BL.xlsx)", type=["xlsx"])

    if uploaded_file is not None:
        try:
            xls = pd.ExcelFile(uploaded_file)
            data = {sheet: pd.read_excel(xls, sheet) for sheet in xls.sheet_names}
            st.session_state["data_xlsx"] = data
            st.success(f"✅ {len(xls.sheet_names)} feuilles chargées : {', '.join(xls.sheet_names)}")
        except Exception as e:
            st.error(f"Erreur lors du chargement : {e}")

    elif not data:
        st.warning("⚠️ Aucun fichier chargé. Téléversez le fichier Excel pour initialiser l’application.")
        return

    st.markdown("---")
    st.subheader("📑 Vérification du contenu")

    if data:
        sheets = list(data.keys())
        st.write(f"**Feuilles disponibles :** {', '.join(sheets)}")
        st.dataframe(pd.DataFrame({
            "Feuille": sheets,
            "Nombre de lignes": [len(df) for df in data.values()]
        }))
    else:
        st.info("Aucune feuille chargée actuellement.")

    st.markdown("---")
    st.subheader("💾 Export complet du fichier Excel")

    if data:
        if st.button("📤 Générer une copie du fichier Excel"):
            try:
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine="openpyxl") as writer:
                    for sheet_name, df in data.items():
                        df.to_excel(writer, sheet_name=sheet_name, index=False)
                st.download_button(
                    label="📥 Télécharger le fichier Excel complet",
                    data=output.getvalue(),
                    file_name="Export_Clients_BL.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            except Exception as e:
                st.error(f"Erreur lors de la création du fichier : {e}")

    st.markdown("---")
    st.subheader("🧹 Réinitialiser les données de la session")

    if st.button("🗑️ Réinitialiser la session"):
        st.session_state["data_xlsx"] = {}
        st.success("Session réinitialisée. Rechargez l’application.")
        st.experimental_rerun()
