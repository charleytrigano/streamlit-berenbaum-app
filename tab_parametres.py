import streamlit as st
import pandas as pd
from utils_gdrive_oauth import get_gdrive_service
from utils_gdrive_oauth import upload_to_drive, download_from_drive

def tab_parametres():
    st.title("⚙️ Paramètres (Google Drive)")
    st.markdown("Connecte-toi et teste la synchronisation Drive.")

    if st.button("🔐 Se connecter à Google Drive"):
        try:
            service = get_gdrive_service()
            about = service.about().get(fields="user").execute()
            user = about.get("user", {})
            st.success(f"✅ Connecté en tant que **{user.get('displayName','?')}** ({user.get('emailAddress','?')})")
        except Exception as e:
            st.error(f"❌ Erreur OAuth : {e}")

    st.divider()
    st.subheader("📤 Test upload (fichier de test)")
    if st.button("Uploader 'TestUpload.xlsx'"):
        df = pd.DataFrame({"Nom":["Alice","Bob"],"Montant":[1000,800]})
        upload_to_drive({"Test":df}, filename="TestUpload.xlsx")

    st.subheader("📥 Test download (fichier de test)")
    if st.button("Télécharger 'TestUpload.xlsx'"):
        data = download_from_drive("TestUpload.xlsx")
        if data and "Test" in data:
            st.dataframe(data["Test"])
        else:
            st.warning("Fichier introuvable sur Drive.")
