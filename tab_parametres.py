import streamlit as st
import os
import dropbox

def tab_parametres():
    """Onglet Paramètres et intégration Dropbox"""
    st.header("⚙️ Paramètres de l’application")

    st.markdown("### 🔐 Connexion Dropbox")

    # Récupération du token Dropbox depuis les secrets Streamlit ou les variables d'environnement
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
        # Connexion à Dropbox
        dbx = dropbox.Dropbox(token)
        account = dbx.users_get_current_account()

        st.success(f"✅ Connecté à Dropbox en tant que **{account.name.display_name}**")
        st.caption(f"Adresse e-mail : {account.email}")

        # Option : afficher les fichiers récents du dossier courant
        st.markdown("### 📂 Fichiers disponibles sur Dropbox")

        try:
            folder_path = "/"
            files = dbx.files_list_folder(folder_path).entries
            if not files:
                st.info("Aucun fichier trouvé dans ce dossier Dropbox.")
            else:
                for f in files[:10]:  # limite à 10 fichiers
                    if isinstance(f, dropbox.files.FileMetadata):
                        st.write(f"📄 **{f.name}** — {f.size/1024:.1f} Ko")
                    elif isinstance(f, dropbox.files.FolderMetadata):
                        st.write(f"📁 **{f.name}/**")
        except Exception as err:
            st.warning(f"⚠️ Impossible d’afficher la liste des fichiers : {err}")

        st.markdown("---")
        st.caption("💡 Si la connexion échoue, régénère ton token Dropbox dans https://www.dropbox.com/developers/apps")

    except dropbox.exceptions.AuthError as e:
        st.error("🚫 Token Dropbox invalide ou expiré. Vérifie ton token dans Streamlit Secrets.")
        st.exception(e)
    except Exception as e:
        st.error("❌ Erreur lors de la connexion à Dropbox :")
        st.exception(e)
