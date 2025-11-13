import streamlit as st
import pandas as pd
from utils_gdrive_oauth import download_from_drive, upload_to_drive

MAIN_FILE = "Clients BL.xlsx"   # Nom du fichier principal sur Google Drive

# mapping des colonnes pour uniformiser partout
column_map = {
    "Dossier N": "Dossier N",
    "Nom": "Nom",
    "Date": "Date",
    "Categories": "Catégories",
    "Sous-categorie": "Sous-catégorie",
    "Visa": "Visa",
    "Montant honoraires (US $)": "Montant honoraires (US $)",
    "Autres frais (US $)": "Autres frais (US $)",
    "Acompte 1": "Acompte 1",
    "Date Acompte 1": "Date Acompte 1",
    "Mode Paiement 1": "Mode Paiement 1",
    "Acompte 2": "Acompte 2",
    "Date Acompte 2": "Date Acompte 2",
    "Mode Paiement 2": "Mode Paiement 2",
    "Acompte 3": "Acompte 3",
    "Date Acompte 3": "Date Acompte 3",
    "Mode Paiement 3": "Mode Paiement 3",
    "Acompte 4": "Acompte 4",
    "Date Acompte 4": "Date Acompte 4",
    "Mode Paiement 4": "Mode Paiement 4",
    "Dossier Envoye": "Dossier Envoye",
    "Date Envoye": "Date Envoye",
    "Escrow": "Escrow"
}


def ensure_loaded(filename: str):
    """
    Charge le fichier XLSX depuis Google Drive ou depuis session_state.
    Retourne un dict {sheet_name: dataframe}
    """

    # si déjà chargé en session, renvoyer directement
    if "data_xlsx" in st.session_state:
        return st.session_state["data_xlsx"]

    # essayer de télécharger depuis Drive
    content = download_from_drive(filename)
    if content is not None:
        try:
            excel_data = pd.read_excel(content, sheet_name=None, engine="openpyxl")
            st.session_state["data_xlsx"] = excel_data
            return excel_data
        except Exception as e:
            st.error(f"Erreur lecture XLSX : {e}")

    # sinon, charger un fichier vide par défaut
    empty = {
        "Clients": pd.DataFrame(columns=list(column_map.values())),
        "Visa": pd.DataFrame(),
        "ComptaCli": pd.DataFrame(),
        "Escrow": pd.DataFrame(),
    }

    st.session_state["data_xlsx"] = empty
    return empty


def save_all(data: dict, filename: str = MAIN_FILE):
    """
    Sauvegarde le fichier XLSX complet sur Google Drive
    """
    try:
        import io

        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            for sheet_name, df in data.items():
                df.to_excel(writer, index=False, sheet_name=sheet_name)

        upload_to_drive(buffer.getvalue(), filename)
        return True

    except Exception as e:
        st.error(f"❌ Erreur lors de la sauvegarde : {e}")
        return False
