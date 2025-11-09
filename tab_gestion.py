import streamlit as st
import pandas as pd
from datetime import date
import dropbox
import io
import os

DROPBOX_TOKEN = os.getenv("DROPBOX_TOKEN")
DROPBOX_PATH = "/Clients-BL.xlsx"

def tab_gestion():
    """Onglet de gestion et mise à jour des dossiers existants."""
    st.header("🗂️ Gestion des dossiers")

    if "data_xlsx" not in st.session_state or not st.session_state["data_xlsx"]:
        st.warning("⚠️ Chargez d'abord le fichier Excel via l’onglet 📄 Fichiers.")
        return

    data = st.session_state["data_xlsx"]
    if "Clients" not in data:
        st.error("❌ Feuille 'Clients' absente du fichier Excel.")
        return

    df = data["Clients"].copy()
    if df.empty:
        st.warning("📄 Aucun dossier client.")
        return

    # === Sélection du dossier ===
    st.subheader("🔎 Sélection du dossier")
    col_sel1, col_sel2 = st.columns(2)
    dossier_list = sorted(df["Dossier N"].dropna().astype(str).tolist())
    nom_list = sorted(df["Nom"].dropna().astype(str).tolist())

    sel_dossier = col_sel1.selectbox("Dossier N", options=[""] + dossier_list)
    sel_nom = col_sel2.selectbox("Nom du client", options=[""] + nom_list)

    # Synchronisation automatique
    dossier_data = None
    if sel_dossier:
        dossier_data = df[df["Dossier N"].astype(str) == sel_dossier].iloc[0].to_dict()
    elif sel_nom:
        dossier_data = df[df["Nom"].astype(str) == sel_nom].iloc[0].to_dict()

    if dossier_data is None:
        st.info("Sélectionnez un dossier pour le modifier.")
        return

    # === Informations principales ===
    st.subheader("🧾 Informations principales")
    c1, c2, c3 = st.columns(3)
    dossier_n = c1.text_input("Dossier N", value=dossier_data.get("Dossier N", ""))
    nom_client = c2.text_input("Nom du client", value=dossier_data.get("Nom", ""))
    date_creation = c3.date_input(
        "Date (création)",
        value=pd.to_datetime(dossier_data.get("Date création", date.today()), errors="coerce") or date.today()
    )

    # === Classification ===
    st.subheader("📂 Classification et visa")
    col1, col2, col3 = st.columns(3)

    # Lecture du tableau Visa
    df_visa = data.get("Visa", pd.DataFrame())
    categories = sorted(df_visa["Catégorie"].dropna().unique().tolist()) if "Catégorie" in df_visa else []
    selected_cat = col1.selectbox("Catégorie", options=[""] + categories, index=([""] + categories).index(dossier_data.get("Catégories", "")) if dossier_data.get("Catégories", "") in categories else 0)

    souscats = []
    if selected_cat and "Sous-catégorie" in df_visa:
        souscats = sorted(df_visa[df_visa["Catégorie"] == selected_cat]["Sous-catégorie"].dropna().unique().tolist())
    selected_souscat = col2.selectbox("Sous-catégorie", options=[""] + souscats, index=([""] + souscats).index(dossier_data.get("Sous-catégories", "")) if dossier_data.get("Sous-catégories", "") in souscats else 0)

    visas = sorted(df_visa.columns[3:].tolist()) if not df_visa.empty else []
    selected_visa = col3.selectbox("Visa", options=[""] + visas, index=([""] + visas).index(dossier_data.get("Visa", "")) if dossier_data.get("Visa", "") in visas else 0)

    # === Acomptes ===
    st.subheader("💰 Acomptes")
    for i in range(1, 5):
        c1, c2, c3 = st.columns(3)
        montant = dossier_data.get(f"Acompte {i}", 0.0)
        date_a = dossier_data.get(f"Date Acompte {i}", None)
        c1.number_input(f"Acompte {i} (US $)", min_value=0.0, step=100.0, format="%.2f", key=f"mnt{i}", value=float(montant or 0))
        c2.date_input(f"Date Acompte {i}", value=pd.to_datetime(date_a, errors="coerce") if pd.notna(date_a) else date.today(), key=f"date{i}")
        c3.multiselect(f"Mode paiement Acompte {i}", ["Chèque", "Virement", "Carte bancaire", "Venmo"], key=f"mode{i}")

    # === Escrow ===
    st.subheader("🛡️ Escrow")
    escrow = st.checkbox("Envoyé en Escrow", value=(dossier_data.get("Escrow", "").lower() == "oui"))

    # === Envoi du dossier ===
    st.subheader("📤 Envoi du dossier")
    col_e1, col_e2 = st.columns(2)
    envoye = col_e1.checkbox("Dossier envoyé", value=(str(dossier_data.get("Dossier envoyé", "")).lower() == "oui"))
    date_envoi = col_e2.date_input("Date envoi", value=pd.to_datetime(dossier_data.get("Date envoi", date.today()), errors="coerce") if dossier_data.get("Date envoi") else date.today())

    # Si coché => retirer de l’Escrow
    if envoye:
        escrow = False

    # === Commentaires ===
    st.subheader("📝 Commentaires")
    commentaires = st.text_area("Commentaires", value=dossier_data.get("Commentaires", ""))

    st.markdown("---")

    # === Sauvegarde ===
    if st.button("💾 Enregistrer les modifications"):
        idx = df.index[df["Dossier N"].astype(str) == str(dossier_n)]
        if not idx.empty:
            i = idx[0]
            df.loc[i, "Nom"] = nom_client
            df.loc[i, "Date création"] = date_creation.strftime("%Y-%m-%d")
            df.loc[i, "Catégories"] = selected_cat
            df.loc[i, "Sous-catégories"] = selected_souscat
            df.loc[i, "Visa"] = selected_visa
            df.loc[i, "Escrow"] = "Oui" if escrow else "Non"
            df.loc[i, "Dossier envoyé"] = "Oui" if envoye else "Non"
            df.loc[i, "Date envoi"] = date_envoi.strftime("%Y-%m-%d")
            df.loc[i, "Commentaires"] = commentaires

            # Sauvegarde des acomptes
            for j in range(1, 5):
                df.loc[i, f"Acompte {j}"] = st.session_state.get(f"mnt{j}", 0.0)
                df.loc[i, f"Date Acompte {j}"] = st.session_state.get(f"date{j}", date.today())
                modes = st.session_state.get(f"mode{j}", [])
                df.loc[i, f"Mode paiement {j}"] = ", ".join(modes)

            st.session_state["data_xlsx"]["Clients"] = df

            # Sauvegarde Dropbox
            try:
                if DROPBOX_TOKEN:
                    dbx = dropbox.Dropbox(DROPBOX_TOKEN)
                    with io.BytesIO() as buffer:
                        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                            for sheet_name, sheet_df in data.items():
                                if sheet_name == "Clients":
                                    df.to_excel(writer, sheet_name=sheet_name, index=False)
                                else:
                                    sheet_df.to_excel(writer, sheet_name=sheet_name, index=False)
                        buffer.seek(0)
                        dbx.files_upload(buffer.read(), DROPBOX_PATH, mode=dropbox.files.WriteMode.overwrite)
                    st.success("✅ Modifications sauvegardées sur Dropbox.")
                else:
                    st.warning("⚠️ Aucun token Dropbox trouvé — modifications locales uniquement.")
            except Exception as e:
                st.error(f"❌ Erreur Dropbox : {e}")

            st.success("✅ Dossier mis à jour avec succès.")
        else:
            st.error("❌ Dossier introuvable.")
