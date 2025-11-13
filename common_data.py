import io
import pandas as pd
import streamlit as st
from utils_gdrive_oauth import upload_to_drive, download_from_drive

MAIN_FILE = "Clients BL.xlsx"

# Cache principal des données
if "data_xlsx" not in st.session_state:
    st.session_state["data_xlsx"] = {}


# -----------------------------------------------------
#  CHARGEMENT DEPUIS GOOGLE DRIVE
# -----------------------------------------------------
def ensure_loaded(filename=MAIN_FILE):
    """Charge le fichier Excel principal depuis Drive et le met en cache Streamlit."""
    if "data_xlsx" in st.session_state and st.session_state["data_xlsx"]:
        return st.session_state["data_xlsx"]

    data_bytes = download_from_drive(filename)
    if not data_bytes:
        st.warning(f"⚠️ Fichier {filename} introuvable ou vide.")
        return {}

    try:
        excel_data = pd.read_excel(io.BytesIO(data_bytes), sheet_name=None)
        st.session_state["data_xlsx"] = excel_data
        st.success(f"✅ Données chargées depuis {filename}")
        return excel_data
    except Exception as e:
        st.error(f"❌ Erreur lecture Excel : {e}")
        return {}


# -----------------------------------------------------
#  SAUVEGARDE VERS GOOGLE DRIVE (VERSION SÛRE)
# -----------------------------------------------------
def save_all(data_dict=None, filename=MAIN_FILE):
    """
    Sauvegarde sécurisée sur Google Drive.
    Empêche le bug 'At least one sheet must be visible'
    """
    if data_dict is None:
        data_dict = st.session_state.get("data_xlsx", {})

    if not data_dict:
        st.warning("⚠️ Aucun jeu de données à sauvegarder.")
        return False

    try:
        # ✅ Construction sécurisée
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            wrote = False
            for sheet, df in data_dict.items():
                if df is None or df.empty:
                    pd.DataFrame({"": []}).to_excel(writer, sheet_name=str(sheet or "Sheet1"), index=False)
                else:
                    df.to_excel(writer, sheet_name=str(sheet or "Sheet1"), index=False)
                wrote = True

            if not wrote:
                pd.DataFrame({"": []}).to_excel(writer, sheet_name="Sheet1", index=False)

        output.seek(0)

        # ✅ Appel Drive sécurisé
        upload_to_drive(data_dict, filename)
        st.success(f"💾 Sauvegarde complète sur Drive : {filename}")
        return True

    except Exception as e:
        st.error(f"❌ Erreur lors de la sauvegarde : {e}")
        return False