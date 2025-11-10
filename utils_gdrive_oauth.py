import streamlit as st
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload
import pandas as pd
import io

# Portée minimale : accès aux fichiers créés/utilisés par l'app
SCOPES = ["https://www.googleapis.com/auth/drive.file"]

def _ensure_oauth_config():
    if "gcp_oauth" not in st.secrets:
        raise RuntimeError("Secret [gcp_oauth] manquant. Ajoute client_id et client_secret dans Secrets.")
    if not st.secrets["gcp_oauth"].get("client_id") or not st.secrets["gcp_oauth"].get("client_secret"):
        raise RuntimeError("client_id / client_secret manquants dans [gcp_oauth].")

def get_gdrive_service():
    """Lance le flux OAuth la 1re fois, puis réutilise le token en session."""
    _ensure_oauth_config()
    creds = st.session_state.get("gdrive_token")
    if not creds:
        flow = InstalledAppFlow.from_client_config(
            {
                "installed": {
                    "client_id": st.secrets["gcp_oauth"]["client_id"],
                    "client_secret": st.secrets["gcp_oauth"]["client_secret"],
                    "redirect_uris": ["https://localhost"],
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token"
                }
            }, SCOPES
        )
        # Ouvre un port local (ok sur Streamlit Cloud)
        creds = flow.run_local_server(port=0)
        st.session_state["gdrive_token"] = creds
    return build("drive", "v3", credentials=creds)

def _find_file(service, filename, parent_id=None):
    q = f"name = '{filename.replace(\"'\", \"\\'\")}' and trashed = false"
    if parent_id:
        q += f" and '{parent_id}' in parents"
    res = service.files().list(q=q, fields="files(id,name,parents)").execute()
    files = res.get("files", [])
    return files[0] if files else None

def upload_to_drive(data_dict, filename="Clients BL.xlsx", parent_id=None):
    """Écrit le classeur (dict de DataFrames) vers Drive (création/mise à jour)."""
    service = get_gdrive_service()

    # buffer xlsx
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        for sheet, df in data_dict.items():
            # sécurité : convertir les colonnes de dates en str ISO au besoin
            safe = df.copy()
            for c in safe.columns:
                if str(safe[c].dtype).startswith("datetime64"):
                    safe[c] = safe[c].dt.date.astype(str)
            safe.to_excel(writer, sheet_name=sheet[:31], index=False)
    output.seek(0)

    media = MediaIoBaseUpload(
        output,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    found = _find_file(service, filename, parent_id)
    if found:
        service.files().update(fileId=found["id"], media_body=media).execute()
        st.toast(f"✅ Fichier mis à jour sur Drive : {filename}", icon="💾")
        return found["id"]
    else:
        meta = {"name": filename}
        if parent_id:
            meta["parents"] = [parent_id]
        created = service.files().create(body=meta, media_body=media, fields="id").execute()
        st.toast(f"✅ Fichier créé sur Drive : {filename}", icon="🆕")
        return created["id"]

def download_from_drive(filename="Clients BL.xlsx", parent_id=None):
    """Lit un classeur depuis Drive → dict(sheet_name->DataFrame)."""
    service = get_gdrive_service()
    found = _find_file(service, filename, parent_id)
    if not found:
        st.warning(f"⚠️ Fichier introuvable sur Drive : {filename}")
        return None

    req = service.files().get_media(fileId=found["id"])
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, req)
    done = False
    while not done:
        status, done = downloader.next_chunk()
    fh.seek(0)
    return pd.read_excel(fh, sheet_name=None)
