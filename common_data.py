import streamlit as st
import pandas as pd
from utils_gdrive_oauth import download_from_drive, upload_to_drive

# --------------------------------------------------------
# Nom du fichier principal
# --------------------------------------------------------
MAIN_FILE = "Clients BL.xlsx"

# --------------------------------------------------------
# Chargement des données depuis Google Drive
# --------------------------------------------------------
def ensure_loaded(filename=MAIN_FILE):
    """
    Charge le fichier Excel depuis Drive si pas déjà en mémoire.
    """
    if "data_xlsx" in st.session_state:
        return st.session_state["data_xlsx"]

    try:
        content = download_from_drive(filename)
        df_dict = pd.read_excel(content, sheet_name=None)
        st.session_state["data_xlsx"] = df_dict
        return df_dict
    except Exception as e:
        st.error(f"❌ Impossible de charger {filename} : {e}")
        return {}

# --------------------------------------------------------
# Sauvegarde vers Google Drive
# --------------------------------------------------------
def save_all(data_dict=None):
    """
    Sauvegarde toutes les feuilles Excel dans Google Drive.
    """
    if data_dict is None:
        data_dict = st.session_state.get("data_xlsx", {})

    try:
        output = pd.ExcelWriter("temp.xlsx", engine="openpyxl")

        for sheet, df in data_dict.items():
            df.to_excel(output, index=False, sheet_name=sheet)

        output.close()

        with open("temp.xlsx", "rb") as f:
            upload_to_drive(f, MAIN_FILE)

        st.success("✅ Sauvegarde réussie sur Google Drive.")

    except Exception as e:
        st.error(f"❌ Erreur lors de la sauvegarde : {e}")
