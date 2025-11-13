import os
import io
import json
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/drive.file"]

TOKEN_FILE = "token.json"
CREDENTIALS_FILE = "credentials.json"

def get_credentials():
    """Charge ou crée les identifiants OAuth 2.0"""
    creds = None

    # Charger token.json si existe
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    # S'il n'existe pas, lancer l'OAuth Google
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=8089)

        # Sauvegarde token.json
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())

    return creds


def get_service():
    """Retourne un service Google Drive authentifié"""
    creds = get_credentials()
    return build("drive", "v3", credentials=creds)


def download_from_drive(filename):
    """Retourne les BYTES d’un fichier Drive"""
    service = get_service()

    query = f"name='{filename}' and trashed=false"
    results = service.files().list(q=query, fields="files(id, name)").execute()
    files = results.get("files", [])

    if not files:
        return None

    file_id = files[0]["id"]
    request = service.files().get_media(fileId=file_id)
    buffer = io.BytesIO()

    downloader = MediaIoBaseDownload(buffer, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()

    buffer.seek(0)
    return buffer.read()


def upload_to_drive(content_bytes, filename):
    """Envoie un fichier (bytes) sur Google Drive"""
    service = get_service()

    # Convertir bytes en buffer
    if isinstance(content_bytes, bytes):
        stream = io.BytesIO(content_bytes)
    else:
        stream = content_bytes  # buffer déjà fourni

    # Vérifier si le fichier existe déjà
    query = f"name='{filename}' and trashed=false"
    results = service.files().list(q=query, fields="files(id)").execute()
    existing = results.get("files", [])

    media = MediaIoBaseUpload(stream, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    if existing:
        service.files().update(fileId=existing[0]["id"], media_body=media).execute()
    else:
        service.files().create(body={"name": filename}, media_body=media).execute()
