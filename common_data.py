import streamlit as st
import pandas as pd
from utils_gdrive_oauth import download_from_drive, upload_to_drive

DEFAULT_FILE = "Clients BL.xlsx"

REQUIRED_SHEETS = {
    "Clients": [
        "Dossier N","Nom","Date","Catégories","Sous-catégories","Visa",
        "Montant honoraires (US $)","Acompte 1","Date Acompte 1","Mode de paiement",
        "Escrow","Dossier envoyé","Date envoi","Dossier accepté","Date acceptation",
        "Dossier refusé","Date refus","Dossier annulé","Date annulation","RFE","Commentaires"
    ],
    "Visa": [
        "Catégories","Sous-catégories","Visa"
    ],
    "ComptaCli": [],  # si vide, on laisse tel quel
    "Escrow": ["Dossier N","Nom","Montant","Date envoi","Etat","Date réclamation"]
}

def ensure_loaded(filename=DEFAULT_FILE):
    """Charge data_xlsx en session depuis Drive si absent, et garantit les feuilles minimales."""
    if "data_xlsx" not in st.session_state or not st.session_state["data_xlsx"]:
        data = download_from_drive(filename)
        if data is None:
            data = {}
        # normaliser
        for sheet, cols in REQUIRED_SHEETS.items():
            if sheet not in data or not isinstance(data[sheet], pd.DataFrame):
                data[sheet] = pd.DataFrame(columns=cols)
            else:
                # s'assurer que les colonnes essentielles existent
                for c in cols:
                    if c not in data[sheet].columns:
                        data[sheet][c] = pd.Series([], dtype="object")
        st.session_state["data_xlsx"] = data
    return st.session_state["data_xlsx"]

def save_all(filename=DEFAULT_FILE):
    """Sauvegarde le data_xlsx courant sur Drive."""
    data = st.session_state.get("data_xlsx", None)
    if data:
        upload_to_drive(data, filename)
