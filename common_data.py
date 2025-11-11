import os
import pandas as pd
import streamlit as st
from utils_gdrive_oauth import download_from_drive, upload_to_drive

# 🔧 Dictionnaire global contenant toutes les données Excel
DATA_CACHE = {}

def load_excel_data(local_path):
    """Charge le contenu d’un fichier Excel local dans un dictionnaire de DataFrames."""
    if not os.path.exists(local_path):
        st.warning(f"⚠️ Fichier introuvable localement : {local_path}")
        return {}
    try:
        xls = pd.ExcelFile(local_path)
        data = {sheet: pd.read_excel(xls, sheet_name=sheet) for sheet in xls.sheet_names}
        return data
    except Exception as e:
        st.error(f"❌ Erreur lors du chargement du fichier Excel : {e}")
        return {}

def ensure_loaded(filename="Clients BL.xlsx"):
    """
    Vérifie que les données Excel sont chargées :
    - Essaie d'abord de les charger localement
    - Si absentes, télécharge depuis Google Drive
    """
    global DATA_CACHE

    if filename in DATA_CACHE:
        return DATA_CACHE[filename]

    local_path = os.path.join(os.getcwd(), filename)

    # 🔹 Si le fichier n’existe pas localement, on tente de le récupérer sur Drive
    if not os.path.exists(local_path):
        st.info(f"📥 Téléchargement du fichier '{filename}' depuis Google Drive…")
        success = download_from_drive(filename, local_path)
        if not success:
            st.error("❌ Impossible de récupérer le fichier sur Google Drive.")
            return {}

    data = load_excel_data(local_path)
    DATA_CACHE[filename] = data
    return data

def save_all(data_dict, filename="Clients BL.xlsx"):
    """
    Sauvegarde les données Excel localement et sur Google Drive
    """
    local_path = os.path.join(os.getcwd(), filename)

    try:
        # Sauvegarde locale
        with pd.ExcelWriter(local_path, engine='xlsxwriter') as writer:
            for sheet, df in data_dict.items():
                df.to_excel(writer, sheet_name=sheet, index=False)
        st.success(f"💾 Fichier enregistré localement : {local_path}")

        # Envoi vers Google Drive
        upload_to_drive(local_path, filename)
        st.info("☁️ Sauvegarde Google Drive effectuée avec succès.")
    except Exception as e:
        st.error(f"❌ Erreur lors de la sauvegarde : {e}")
