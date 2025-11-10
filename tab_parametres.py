import streamlit as st
from utils_gdrive_oauth import get_gdrive_service, upload_to_drive, download_from_drive
import pandas as pd

def tab_parametres():
    st.title("⚙️ Paramètres de connexion Google Drive")

    st.markdown("""
    Cette page permet de connecter ton application à Google Drive via OAuth2.
    Une fois connecté, tu pourras sauvegarder et charger ton fichier Excel directement depuis ton Drive.
    """)

    st.divider()

    # Test de connexion
    if st.button("🔐 Se connecter à Google Drive"):
        try:
            service = get_gdrive_service()
            about = service.about().get(fields="user").execute()
            user = about.get("user", {})
            st.success(f"✅ Connecté à Google Drive en tant que **{user.get('displayName', 'Inconnu')}** ({user.get('emailAddress', 'email inconnu')})")
        except Exception as e:
            st.error(f"❌ Erreur de connexion : {e}")

    st.divider()

    # Section test upload
    st.subheader("📤 Test d’upload vers Google Drive")
    if st.button("Uploader un fichier de test"):
        df_test = pd.DataFrame({"Nom": ["Jean", "Marie"], "Montant": [1200, 800]})
        data_dict = {"Test": df_test}
        upload_to_drive(data_dict, "TestUpload.xlsx")

    st.divider()

    # Section test download
    st.subheader("📥 Test de téléchargement depuis Google Drive")
    if st.button("Télécharger le fichier de test"):
        data = download_from_drive("TestUpload.xlsx")
        if data:
            st.write(data["Test"].head())
