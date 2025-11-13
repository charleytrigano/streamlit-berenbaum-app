import streamlit as st
import pandas as pd
import io
from utils_gdrive_oauth import get_gdrive_service

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

# -------------------------------------------------------
# LOAD XLSX FROM BYTES
# -------------------------------------------------------
def load_xlsx(file_bytes):
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


# -------------------------------------------------------
# SAVE LOCALLY (Memory)
# -------------------------------------------------------
def save_all_local(data_dict):
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


# -------------------------------------------------------
# SAVE TO GOOGLE DRIVE
# -------------------------------------------------------
def save_all(data_dict, filename=MAIN_FILE):
    """Sauvegarde sur Google Drive si token OK, sinon local uniquement."""
    service = get_gdrive_service()

    # Export XLSX en mémoire
    output = io.BytesIO()
    try:
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            for sheet, df in data_dict.items():
                if not isinstance(df, pd.DataFrame) or df.empty:
                    df = pd.DataFrame({" ": []})
                df.to_excel(writer, sheet_name=sheet, index=False)
        output.seek(0)
    except Exception as e:
        st.error(f"Erreur conversion XLSX : {e}")
        return False

    # Si Google Drive est OK → upload
    if service:
        try:
            from googleapiclient.http import MediaIoBaseUpload

            file_id = None
            search = service.files().list(
                q=f"name='{filename}' and trashed=false",
                spaces="drive",
                fields="files(id)"
            ).execute()

            if search["files"]:
                file_id = search["files"][0]["id"]

            media = MediaIoBaseUpload(output, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

            if file_id:
                service.files().update(fileId=file_id, media_body=media).execute()
            else:
                service.files().create(
                    body={"name": filename},
                    media_body=media
                ).execute()

            return True

        except Exception as e:
            st.error(f"Erreur sauvegarde Google Drive : {e}")
            st.warning("Sauvegarde locale uniquement.")
            return save_all_local(data_dict)

    # Pas de token Google → sauvegarde locale
    return save_all_local(data_dict)


# -------------------------------------------------------
# ENSURE FILE LOADED
# -------------------------------------------------------
def ensure_loaded(filename=MAIN_FILE):
    """Charge le fichier dans session_state si pas encore fait."""
    if "data_xlsx" in st.session_state:
        return st.session_state["data_xlsx"]

    st.warning("⚠️ Fichier non chargé — veuillez l'importer via l’onglet Fichiers.")
    return None