import os
import io
import pickle
import streamlit as st
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload
from google.auth.transport.requests import Request

# Autorisation limitée à l'accès aux fichiers créés par l'app
SCOPES = ["https://www.googleapis.com/auth/drive.file"]
TOKEN_FILE = "token_gdrive.pkl"
CREDENTIALS_FILE = "credentials.json"


def get_gdrive_service():
    """Authentifie l'utilisateur et retourne un service Google Drive actif."""
    creds = None
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "rb") as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_FILE):
                st.error("⚠️ Fichier 'credentials.json' manquant. Télécharge-le depuis Google Cloud Console.")
                return None
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "wb") as token:
            pickle.dump(creds, token)

    return build("drive", "v3", credentials=creds)


def upload_to_drive(local_path, drive_filename):
    """Envoie un fichier vers Google Drive"""
    service = get_gdrive_service()
    if not service:
        return False
    file_metadata = {"name": drive_filename}
    media = MediaIoBaseUpload(open(local_path, "rb"), mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    service.files().create(body=file_metadata, media_body=media, fields="id").execute()
    st.success(f"✅ Fichier '{drive_filename}' uploadé sur Google Drive")
    return True


def download_from_drive(file_name, local_path):
    """Télécharge un fichier de Google Drive"""
    service = get_gdrive_service()
    if not service:
        return False
    results = service.files().list(q=f"name='{file_name}' and trashed=false", fields="files(id, name)").execute()
    items = results.get("files", [])
    if not items:
        st.warning("❌ Fichier non trouvé sur Google Drive.")
        return False
    file_id = items[0]["id"]
    request = service.files().get_media(fileId=file_id)
    with open(local_path, "wb") as f:
        downloader = MediaIoBaseDownload(f, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
    st.success(f"✅ Fichier '{file_name}' téléchargé dans '{local_path}'")
    return True
