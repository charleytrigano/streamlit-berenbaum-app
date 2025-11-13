import os
import json
import io
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload

SCOPES = ["https://www.googleapis.com/auth/drive.file"]

TOKEN_FILE = "token.json"
CREDENTIALS_FILE = "credentials.json"


def load_credentials():
    """Charge les credentials depuis token.json et credentials.json"""
    if not os.path.exists(TOKEN_FILE):
        raise FileNotFoundError("token.json manquant. Exécute generate_token.py")

    with open(TOKEN_FILE, "r") as f:
        token_data = json.load(f)

    with open(CREDENTIALS_FILE, "r") as f:
        cred_data = json.load(f)["installed"]

    creds = Credentials(
        token=token_data.get("token"),
        refresh_token=token_data.get("refresh_token"),
        token_uri=cred_data["token_uri"],
        client_id=cred_data["client_id"],
        client_secret=cred_data["client_secret"],
        scopes=SCOPES,
    )
    return creds


def get_service():
    """Retourne un service Drive API authentifié"""
    creds = load_credentials()
    return build("drive", "v3", credentials=creds)


def find_file_id(filename: str):
    """Retourne l'ID du fichier sur Drive si trouvé"""
    service = get_service()
    query = f"name = '{filename}' and trashed = false"

    results = service.files().list(q=query, fields="files(id, name)").execute()
    files = results.get("files", [])

    return files[0]["id"] if files else None


def download_from_drive(filename: str):
    """Télécharge un fichier Google Drive et renvoie ses bytes"""
    try:
        file_id = find_file_id(filename)
        if not file_id:
            return None

        service = get_service()
        request = service.files().get_media(fileId=file_id)

        buffer = io.BytesIO()
        downloader = MediaIoBaseDownload(buffer, request)

        done = False
        while not done:
            _, done = downloader.next_chunk()

        return buffer.getvalue()

    except Exception as e:
        print("Erreur download_from_drive :", e)
        return None


def upload_to_drive(file_bytes: bytes, filename: str):
    """Upload un fichier binaire vers Google Drive (overwrite)"""
    try:
        service = get_service()

        file_id = find_file_id(filename)

        media = MediaIoBaseUpload(io.BytesIO(file_bytes), mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        if file_id:
            service.files().update(fileId=file_id, media_body=media).execute()
        else:
            file_metadata = {"name": filename}
            service.files().create(body=file_metadata, media_body=media).execute()

        print("Upload réussi :", filename)
        return True

    except Exception as e:
        print("Erreur upload_to_drive :", e)
        return False

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
import json
import os

SCOPES = ["https://www.googleapis.com/auth/drive.file"]

def get_gdrive_service():
    """Charge token.json, rafraîchit si nécessaire et retourne le service Drive."""
    
    if not os.path.exists("token.json"):
        raise FileNotFoundError("token.json manquant — génère le token d’abord.")

    with open("token.json", "r") as f:
        token_data = json.load(f)

    creds = Credentials.from_authorized_user_info(token_data, SCOPES)

    # Rafraîchissement automatique si expiré
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open("token.json", "w") as f:
            f.write(creds.to_json())

    # Retourne l'API Drive
    return build("drive", "v3", credentials=creds)

