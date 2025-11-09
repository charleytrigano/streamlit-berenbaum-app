import streamlit as st
import os
import dropbox
from io import BytesIO

def tab_parametres():
    """Onglet Paramètres et intégration Dropbox"""
    st.header("⚙️ Paramètres de l’application")

    st.markdown("### 🔐 Connexion Dropbox")

    # Récupération du token Dropbox
    token = os.getenv("DROPBOX_TOKEN") or st.secrets.get("DROPBOX_TOKEN")

    if not token:
        st.error("❌ Aucun token Dropbox trouvé. Ajoute ton token dans Streamlit Cloud (Settings → Secrets).")
        st.info("""
        Exemple :
        ```
        DROPBOX_TOKEN = "sl.xxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
        ```
        """)
        return

    try:
        # Connexion Dropbox
        dbx = dropbox.Dropbox(token)
        account = dbx.users_get_current_account()

        st.success(f"✅ Connecté à Dropbox en tant que **{account.name.display_name}**")
        st.caption(f"Adresse e-mail : {account.email}")

        st.markdown("### 📂 Fichiers disponibles sur Dropbox")

        try:
            # ✅ Correction ici : chemin vide = racine Dropbox
            result = dbx.files_list_folder(path="")
            files = result.entries

            if not files:
                st.info("Aucun fichier trouvé dans la racine Dropbox.")
            else:
                for f in files[:10]:
                    if isinstance(f, dropbox.files.FileMetadata):
                        st.write(f"📄 **{f.name}** — {f.size/1024:.1f} Ko")
                    elif isinstance(f, dropbox.files.FolderMetadata):
                        st.write(f"📁 **{f.name}/**")

        except Exception as err:
            st.warning(f"⚠️ Impossible d’afficher la liste des fichiers : {err}")

        # --- 🔼 Téléversement vers Dropbox ---
        st.markdown("---")
        st.markdown("### ⬆️ Téléverser un fichier vers Dropbox")

        uploaded_file = st.file_uploader("Sélectionne un fichier à envoyer :", type=["xlsx", "csv", "txt", "pdf", "docx"])

        if uploaded_file is not None:
            dropbox_path = st.text_input(
                "Chemin de destination sur Dropbox (ex: /Clients-BL.xlsx)",
                value=f"/{uploaded_file.name}"
            )

            if st.button("📤 Envoyer vers Dropbox"):
                try:
                    dbx.files_upload(
                        uploaded_file.getvalue(),
                        dropbox_path,
                        mode=dropbox.files.WriteMode("overwrite")
                    )
                    st.success(f"✅ Fichier envoyé avec succès : `{dropbox_path}`")
                except Exception as e:
                    st.error(f"⚠️ Erreur lors de l'envoi : {e}")

        st.markdown("---")
        st.caption("💡 Si la connexion échoue, régénère ton token Dropbox dans https://www.dropbox.com/developers/apps")

    except dropbox.exceptions.AuthError:
        st.error("🚫 Token Dropbox invalide ou expiré. Vérifie ton token dans Streamlit Secrets.")
    except Exception as e:
        st.error("❌ Erreur lors de la connexion à Dropbox :")
        st.exception(e)
