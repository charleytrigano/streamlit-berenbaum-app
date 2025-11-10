import streamlit as st
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload
import pandas as pd
import io

SCOPES = ["https://www.googleapis.com/auth/drive.file"]

def get_gdrive_service():
    """Authentifie l'utilisateur via OAuth et retourne le service Drive."""
    creds = None

    # Si déjà authentifié dans la session
    if "gdrive_token" in st.session_state:
        creds = st.session_state["gdrive_token"]
    else:
        flow = InstalledAppFlow.from_client_config(
            {
                "installed": {
                    "client_id": st.secrets["gcp_oauth"]["client_id"],
                    "client_secret": st.secrets["gcp_oauth"]["client_secret"],
                    "redirect_uris": ["https://localhost"],
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token"
                }
            },
            SCOPES
        )
        creds = flow.run_local_server(port=0)
        st.session_state["gdrive_token"] = creds

    return build("drive", "v3", credentials=creds)

def upload_to_drive(data_dict, filename="Clients BL.xlsx"):
    """Sauvegarde du fichier Excel sur Google Drive."""
    try:
        service = get_gdrive_service()

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            for sheet, df in data_dict.items():
                df.to_excel(writer, sheet_name=sheet, index=False)
        output.seek(0)

        media = MediaIoBaseUpload(
            output,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        # Vérifier si le fichier existe déjà
        query = f"name='{filename}'"
        results = service.files().list(q=query, fields="files(id)").execute()
        files = results.get("files", [])

        if files:
            file_id = files[0]["id"]
            service.files().update(fileId=file_id, media_body=media).execute()
            st.success(f"✅ Fichier mis à jour sur Google Drive : {filename}")
        else:
            file_metadata = {"name": filename}
            service.files().create(
                body=file_metadata,
                media_body=media,
                fields="id"
            ).execute()
            st.success(f"✅ Nouveau fichier ajouté sur Google Drive : {filename}")

    except Exception as e:
        st.error(f"❌ Erreur lors de la sauvegarde sur Google Drive : {e}")

def download_from_drive(filename="Clients BL.xlsx"):
    """Télécharge un fichier Excel depuis Google Drive."""
    try:
        service = get_gdrive_service()
        results = service.files().list(q=f"name='{filename}'", fields="files(id)").execute()
        files = results.get("files", [])
        if not files:
            st.warning(f"⚠️ Fichier {filename} introuvable sur Google Drive.")
            return None

        file_id = files[0]["id"]
        request = service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)

        done = False
        while not done:
            status, done = downloader.next_chunk()

        fh.seek(0)
        data = pd.read_excel(fh, sheet_name=None)
        st.success(f"✅ Fichier téléchargé depuis Google Drive : {filename}")
        return data

    except Exception as e:
        st.error(f"❌ Erreur de téléchargement Google Drive : {e}")
        return None
