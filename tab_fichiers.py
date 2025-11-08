import streamlit as st
import pandas as pd
import os

EXCEL_FILE = "Clients BL.xlsx"

@st.cache_data
def read_excel_file(file_path):
    """Charge toutes les feuilles du fichier Excel."""
    if not os.path.exists(file_path):
        return None
    try:
        xls = pd.ExcelFile(file_path)
        return {sheet: pd.read_excel(xls, sheet_name=sheet) for sheet in xls.sheet_names}
    except Exception as e:
        st.error(f"Erreur lors du chargement du fichier : {e}")
        return None


def tab_fichiers():
    """Gestion et aperçu du fichier Excel principal."""
    st.header("📄 Gestion des fichiers Excel")

    # Vérifie la présence du fichier
    if not os.path.exists(EXCEL_FILE):
        st.warning(f"⚠️ Le fichier `{EXCEL_FILE}` est introuvable dans le dépôt.")
    else:
        st.success(f"✅ Fichier détecté : `{EXCEL_FILE}`")

        # Lecture
        data = read_excel_file(EXCEL_FILE)
        if data:
            st.write(f"**{len(data)} feuilles détectées :**")
            st.write(list(data.keys()))

            # Afficher un aperçu rapide de la feuille Clients si elle existe
            if "Clients" in data:
                st.markdown("### 👁️ Aperçu de la feuille *Clients*")
                st.dataframe(data["Clients"].head(10), use_container_width=True)
            else:
                st.info("La feuille 'Clients' n’a pas été trouvée dans le fichier.")

            # Bouton de téléchargement
            with open(EXCEL_FILE, "rb") as f:
                st.download_button(
                    label="📥 Télécharger le fichier Excel",
                    data=f,
                    file_name=EXCEL_FILE,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

    st.markdown("---")
    st.subheader("📤 Charger un nouveau fichier Excel")

    uploaded = st.file_uploader("Choisissez un fichier Excel", type=["xlsx"])
    if uploaded:
        with open(EXCEL_FILE, "wb") as f:
            f.write(uploaded.getbuffer())
        st.success("✅ Nouveau fichier enregistré avec succès.")
        st.session_state["data_xlsx"] = read_excel_file(EXCEL_FILE)
        st.rerun()

