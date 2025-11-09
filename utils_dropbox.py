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

import streamlit as st
import pandas as pd
import io
import dropbox
import os

def save_xlsx_local(data_dict, filename="Clients_BL.xlsx"):
    """Sauvegarde locale du fichier Excel modifié"""
    try:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            for sheet, df in data_dict.items():
                df.to_excel(writer, sheet_name=sheet, index=False)
        with open(filename, "wb") as f:
            f.write(output.getvalue())
        st.info(f"💾 Fichier sauvegardé localement : {filename}")
    except Exception as e:
        st.error(f"❌ Erreur lors de la sauvegarde locale : {e}")


def save_xlsx_to_dropbox(data_dict, dropbox_path="/Clients-BL.xlsx"):
    """Sauvegarde du fichier Excel sur Dropbox"""
    token = os.getenv("DROPBOX_TOKEN") or st.secrets.get("DROPBOX_TOKEN")
    if not token:
        st.warning("⚠️ Aucun token Dropbox trouvé. Ajoutez-le dans les secrets Streamlit.")
        return

    try:
        dbx = dropbox.Dropbox(token)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            for sheet, df in data_dict.items():
                df.to_excel(writer, sheet_name=sheet, index=False)

        dbx.files_upload(
            output.getvalue(),
            dropbox_path,
            mode=dropbox.files.WriteMode("overwrite")
        )
        st.success(f"✅ Fichier enregistré sur Dropbox : {dropbox_path}")

    except dropbox.exceptions.AuthError:
        st.error("🚫 Token Dropbox invalide ou expiré.")
    except Exception as e:
        st.error(f"❌ Erreur lors de la sauvegarde Dropbox : {e}")

