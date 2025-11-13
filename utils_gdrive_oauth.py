import io
import json
import streamlit as st
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload

SCOPES = ["https://www.googleapis.com/auth/drive.file"]


# -----------------------------------------------------
#  SERVICE GOOGLE DRIVE
# -----------------------------------------------------
def get_gdrive_service():
    """Retourne un service Google Drive authentifié."""
    if "gdrive_token" not in st.secrets:
        st.error("❌ Aucun token Google Drive trouvé dans les secrets Streamlit.")
        return None

    token_data = st.secrets["gdrive_token"]

    try:
        creds = Credentials(
            token=token_data.get("token"),
            refresh_token=token_data.get("refresh_token"),
            client_id=token_data.get("client_id"),
            client_secret=token_data.get("client_secret"),
            token_uri="https://oauth2.googleapis.com/token",
            scopes=SCOPES,
        )
    except Exception as e:
        st.error(f"❌ Impossible de charger les credentials : {e}")
        return None

    try:
        service = build("drive", "v3", credentials=creds)
        return service
    except Exception as e:
        st.error(f"❌ Erreur création service Drive : {e}")
        return None


# -----------------------------------------------------
#  DOWNLOAD
# -----------------------------------------------------
def download_from_drive(filename):
    """Télécharge un fichier Google Drive et retourne son contenu binaire."""
    service = get_gdrive_service()
    if not service:
        return None

    try:
        results = service.files().list(
            q=f"name='{filename}' and trashed=false",
            fields="files(id, name)"
        ).execute()

        files = results.get("files", [])
        if not files:
            st.warning(f"⚠️ Fichier '{filename}' introuvable sur Drive.")
            return None

        file_id = files[0]["id"]
        request = service.files().get_media(fileId=file_id)

        file_data = io.BytesIO()
        downloader = MediaIoBaseDownload(file_data, request)

        done = False
        while not done:
            _, done = downloader.next_chunk()

        file_data.seek(0)
        return file_data.read()

    except Exception as e:
        st.error(f"❌ Erreur téléchargement Drive : {e}")
        return None


# -----------------------------------------------------
#  UPLOAD (VERSION SÛRE)
# -----------------------------------------------------
def upload_to_drive(data_dict, filename="Clients BL.xlsx"):
    """Enregistre un fichier Excel sur Google Drive, SAFE MODE."""

    service = get_gdrive_service()
    if not service:
        return False

    try:
        # 🔒 Construire le fichier Excel en mémoire
        output = io.BytesIO()

        import pandas as pd

        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            for sheet, df in data_dict.items():

                # ⚠️ Patch anti-feuille vide invisible
                if df is None or len(df) == 0:
                    safe_df = pd.DataFrame({"": []})
                    safe_df.to_excel(writer, sheet_name=sheet, index=False)
                else:
                    df.to_excel(writer, sheet_name=sheet, index=False)

        output.seek(0)

        # -----------------------------------------------------
        #  Vérifier si le fichier existe déjà
        # -----------------------------------------------------
        results = service.files().list(
            q=f"name='{filename}' and trashed=false",
            fields="files(id, name)"
        ).execute()

        media = MediaIoBaseUpload(output, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        if results.get("files"):
            # Mise à jour du fichier existant
            file_id = results["files"][0]["id"]
            service.files().update(fileId=file_id, media_body=media).execute()
        else:
            # Nouveau fichier
            file_metadata = {"name": filename}
            service.files().create(body=file_metadata, media_body=media).execute()

        st.success(f"✅ Fichier sauvegardé sur Google Drive : {filename}")
        return True

    except Exception as e:
        st.error(f"❌ Erreur lors de la sauvegarde : {e}")
        return False
