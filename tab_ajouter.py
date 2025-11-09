import streamlit as st
import pandas as pd
from datetime import date
import dropbox
import io
import os

# ===== CONFIGURATION DROPBOX =====
DROPBOX_TOKEN = os.getenv("DROPBOX_TOKEN")  # ⚠️ à définir dans Streamlit Cloud (Secrets)
DROPBOX_PATH = "/Clients-BL.xlsx"

def tab_ajouter():
    """Ajout d'un dossier client."""
    st.header("➕ Ajouter un dossier")

    if "data_xlsx" not in st.session_state or not st.session_state["data_xlsx"]:
        st.warning("⚠️ Chargez d'abord le fichier Excel via l’onglet 📄 Fichiers.")
        return

    data = st.session_state["data_xlsx"]
    if "Clients" not in data or "Visa" not in data:
        st.error("❌ Les feuilles 'Clients' et 'Visa' sont nécessaires.")
        return

    df_clients = data["Clients"].copy()
    df_visa = data["Visa"].copy()

    # === LIGNE 1 ===
    st.subheader("🧾 Informations principales")
    c1, c2, c3 = st.columns(3)
    dossier_n = c1.text_input("Dossier N")
    nom_client = c2.text_input("Nom du client")
    date_creation = c3.date_input("Date (création)", value=date.today())

    # === LIGNE 2 ===
    st.subheader("📂 Classification et visa")
    col1, col2, col3 = st.columns(3)

    categories = sorted(df_visa["Catégorie"].dropna().unique().tolist()) if "Catégorie" in df_visa else []
    selected_cat = col1.selectbox("Catégorie", options=[""] + categories)

    souscats = []
    if selected_cat and "Sous-catégorie" in df_visa:
        souscats = sorted(df_visa[df_visa["Catégorie"] == selected_cat]["Sous-catégorie"].dropna().unique().tolist())
    selected_souscat = col2.selectbox("Sous-catégorie", options=[""] + souscats)

    visas = sorted(df_visa.columns[3:].tolist())  # lecture de la 1ère ligne (entêtes de visas)
    selected_visa = col3.selectbox("Visa", options=[""] + visas)

    # === LIGNE 3 ===
    st.subheader("💵 Informations financières")
    c4, c5, c6 = st.columns(3)
    montant_hono = c4.number_input("Montant honoraires (US $)", min_value=0.0, step=100.0, format="%.2f")
    date_acompte1 = c5.date_input("Date Acompte 1", value=date.today())
    acompte1 = c6.number_input("Acompte 1 (US $)", min_value=0.0, step=100.0, format="%.2f")

    # === LIGNE 4 ===
    st.subheader("💳 Mode de paiement")
    col_mp1, col_mp2, col_mp3, col_mp4 = st.columns(4)
    mode_cheque = col_mp1.checkbox("Chèque")
    mode_virement = col_mp2.checkbox("Virement")
    mode_cb = col_mp3.checkbox("Carte bancaire")
    mode_venmo = col_mp4.checkbox("Venmo")

    mode_paiement = []
    if mode_cheque: mode_paiement.append("Chèque")
    if mode_virement: mode_paiement.append("Virement")
    if mode_cb: mode_paiement.append("Carte bancaire")
    if mode_venmo: mode_paiement.append("Venmo")
    mode_paiement_str = ", ".join(mode_paiement)

    # === LIGNE 5 ===
    st.subheader("🛡️ Escrow")
    escrow = st.checkbox("Envoyer en Escrow")

    # === LIGNE 6 ===
    st.subheader("📝 Commentaires")
    commentaires = st.text_area("Commentaires")

    st.markdown("---")

    # === ENREGISTREMENT ===
    if st.button("💾 Enregistrer le dossier"):
        # Crée une nouvelle ligne
        new_row = {
            "Dossier N": dossier_n,
            "Nom": nom_client,
            "Date création": date_creation.strftime("%Y-%m-%d"),
            "Catégories": selected_cat,
            "Sous-catégories": selected_souscat,
            "Visa": selected_visa,
            "Montant honoraires (US $)": montant_hono,
            "Date Acompte 1": date_acompte1.strftime("%Y-%m-%d"),
            "Acompte 1": acompte1,
            "Mode de paiement": mode_paiement_str,
            "Escrow": "Oui" if escrow else "Non",
            "Commentaires": commentaires
        }

        df_clients = pd.concat([df_clients, pd.DataFrame([new_row])], ignore_index=True)

        # Sauvegarde Dropbox (si token dispo)
        try:
            if DROPBOX_TOKEN:
                dbx = dropbox.Dropbox(DROPBOX_TOKEN)
                with io.BytesIO() as buffer:
                    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                        for sheet_name, sheet_df in data.items():
                            if sheet_name == "Clients":
                                df_clients.to_excel(writer, sheet_name=sheet_name, index=False)
                            else:
                                sheet_df.to_excel(writer, sheet_name=sheet_name, index=False)
                    buffer.seek(0)
                    dbx.files_upload(buffer.read(), DROPBOX_PATH, mode=dropbox.files.WriteMode.overwrite)
                st.success("✅ Dossier ajouté et sauvegardé sur Dropbox.")
            else:
                st.warning("⚠️ Aucun token Dropbox trouvé — le fichier n’a pas été sauvegardé en ligne.")
        except Exception as e:
            st.error(f"❌ Erreur lors de la sauvegarde Dropbox : {e}")

        st.success("✅ Dossier ajouté localement.")
        st.session_state["data_xlsx"]["Clients"] = df_clients
