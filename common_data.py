import streamlit as st
import pandas as pd
import io

MAIN_FILE = "Clients BL.xlsx"

# Colonnes attendues dans chaque feuille
DEFAULT_SHEETS = {
    "Clients": [
        "Dossier N",
        "Nom",
        "Date",
        "Categories",
        "Sous-categorie",
        "Visa",
        "Montant honoraires (US $)",
        "Autres frais (US $)",
        "Acompte 1",
        "Date Acompte 1",
        "Acompte 2",
        "Date Acompte 2",
        "Acompte 3",
        "Date Acompte 3",
        "Acompte 4",
        "Date Acompte 4",
        "Escrow",
        "Dossier envoye",
        "Dossier accepte",
        "Dossier refuse",
        "Dossier annule",
        "RFE",
        "Date RFE",
    ],
    "Visa": [],
    "ComptaCli": [],
    "Escrow": []
}


def load_xlsx(file_bytes):
    """Charge un fichier XLSX uploadé."""
    try:
        xls = pd.ExcelFile(io.BytesIO(file_bytes))
        data = {}

        for sheet, columns in DEFAULT_SHEETS.items():
            if sheet in xls.sheet_names:
                df = pd.read_excel(xls, sheet_name=sheet)
            else:
                df = pd.DataFrame(columns=columns)

            data[sheet] = df

        return data

    except Exception as e:
        st.error(f"Erreur lecture XLSX : {e}")
        return None


def save_all_local(data_dict):
    """Sauvegarde dans session_state sous forme de fichier binaire."""
    try:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            for sheet, df in data_dict.items():
                if not isinstance(df, pd.DataFrame) or df.empty:
                    df = pd.DataFrame({" ": []})
                df.to_excel(writer, sheet_name=sheet, index=False)

        output.seek(0)
        st.session_state["last_saved_file"] = output.getvalue()
        return True

    except Exception as e:
        st.error(f"Erreur sauvegarde locale : {e}")
        return False


def save_all():
    """Sauvegarde simple : met à jour les données et utilise save_all_local."""
    if "data_xlsx" not in st.session_state:
        st.error("❌ Impossible de sauvegarder : aucune donnée chargée.")
        return False

    return save_all_local(st.session_state["data_xlsx"])


def ensure_loaded(filename):
    """Renvoie le fichier chargé ou None si pas encore importé."""
    if "data_xlsx" in st.session_state:
        return st.session_state["data_xlsx"]

    st.warning("⚠️ Fichier non chargé — veuillez l'importer via l’onglet Fichiers.")
    return None