import os
import dropbox
from io import BytesIO

def save_to_dropbox(local_file_path: str, dropbox_path: str):
    """Sauvegarde un fichier local vers Dropbox."""
    token = os.getenv("DROPBOX_TOKEN") or (st.secrets.get("DROPBOX_TOKEN") if "st" in globals() else None)
    if not token:
        st.error("❌ Aucun token Dropbox trouvé.")
        return False

    try:
        dbx = dropbox.Dropbox(token)
        with open(local_file_path, "rb") as f:
            data = f.read()

        dbx.files_upload(
            data,
            dropbox_path,
            mode=dropbox.files.WriteMode("overwrite")
        )

        st.success(f"✅ Fichier sauvegardé sur Dropbox : `{dropbox_path}`")
        return True
    except dropbox.exceptions.AuthError:
        st.error("🚫 Token Dropbox expiré ou invalide. Regénère-le dans les paramètres.")
        return False
    except Exception as e:
        st.error(f"⚠️ Erreur lors de la sauvegarde Dropbox : {e}")
        return False
