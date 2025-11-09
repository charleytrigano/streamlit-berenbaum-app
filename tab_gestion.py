import streamlit as st
import pandas as pd
from datetime import date
from utils_dropbox import, save_xlsx_local

def tab_gestion():
    """Onglet : Gestion des dossiers existants"""
    st.header("📁 Gestion des dossiers clients")

    # --- Réinitialisation propre du dossier sélectionné ---
    if st.session_state.get("reset_gestion"):
        st.session_state.pop("gestion_sel_dossier", None)
        st.session_state.pop("reset_gestion", None)
        st.rerun()

    # Vérification que le fichier Excel est chargé
    if "data_xlsx" not in st.session_state or not st.session_state["data_xlsx"]:
        st.warning("⚠️ Chargez d’abord le fichier Excel via l’onglet 📄 Fichiers.")
        return

    data = st.session_state["data_xlsx"]
    if "Clients" not in data:
        st.error("❌ L’onglet 'Clients' est absent du fichier.")
        return

    df = data["Clients"]

    st.markdown("### 🔍 Sélection d’un dossier")
    c1, c2 = st.columns(2)
    all_dossiers = sorted(df["Dossier N"].dropna().astype(str).unique())
    all_noms = sorted(df["Nom"].dropna().astype(str).unique())

    sel_dossier = c1.selectbox("📄 Dossier N°", [""] + all_dossiers, key="gestion_sel_dossier")
    sel_nom = c2.selectbox("👤 Nom du client", [""] + all_noms, key="gestion_sel_nom")

    if sel_nom and not sel_dossier:
        row = df[df["Nom"] == sel_nom]
    elif sel_dossier:
        row = df[df["Dossier N"] == sel_dossier]
    else:
        row = pd.DataFrame()

    if row.empty:
        st.info("Sélectionnez un dossier ou un nom pour afficher ses informations.")
        return

    dossier_data = row.iloc[0].to_dict()

    st.markdown("### 🧾 Informations du dossier")

    # --- Ligne 1 ---
    c1, c2, c3 = st.columns(3)
    dossier_num = c1.text_input("Dossier N°", value=dossier_data.get("Dossier N", ""))
    nom_client = c2.text_input("Nom du client", value=dossier_data.get("Nom", ""))
    date_creation = c3.date_input(
        "Date (création)",
        value=pd.to_datetime(dossier_data.get("Date création", date.today()), errors="coerce").date() if dossier_data.get("Date création") else date.today(),
        key="gestion_date_creation"
    )

    # --- Ligne 2 ---
    st.markdown("### 📂 Classification")
    visa_sheet = data.get("Visa", pd.DataFrame())

    cats = []
    souscats = []
    visas = []

    if not visa_sheet.empty:
        cats = sorted(visa_sheet["Catégories"].dropna().astype(str).unique().tolist())
        souscats = sorted(visa_sheet["Sous-catégories"].dropna().astype(str).unique().tolist())
        visas = sorted(visa_sheet.columns[visa_sheet.iloc[0] == 1].tolist())

    c1, c2, c3 = st.columns(3)
    cat_sel = c1.selectbox("Catégorie", [""] + cats, index=([""] + cats).index(dossier_data.get("Catégories", "")) if dossier_data.get("Catégories", "") in cats else 0)
    souscat_sel = c2.selectbox("Sous-catégorie", [""] + souscats, index=([""] + souscats).index(dossier_data.get("Sous-catégories", "")) if dossier_data.get("Sous-catégories", "") in souscats else 0)
    visa_sel = c3.selectbox("Visa", [""] + visas, index=([""] + visas).index(dossier_data.get("Visa", "")) if dossier_data.get("Visa", "") in visas else 0)

    # --- Ligne 3 ---
    st.markdown("### 💵 Paiement principal")
    c1, c2, c3 = st.columns(3)
    honoraires = c1.number_input("Montant honoraires (US $)", value=float(dossier_data.get("Montant honoraires (US $)", 0)), min_value=0.0, step=100.0)
    date_acompte1 = c2.date_input("Date Acompte 1", value=pd.to_datetime(dossier_data.get("Date Acompte 1", date.today()), errors='coerce').date() if dossier_data.get("Date Acompte 1") else date.today())
    acompte1 = c3.number_input("Acompte 1", value=float(dossier_data.get("Acompte 1", 0)), min_value=0.0, step=100.0)

    # --- Ligne 4 ---
    st.markdown("### 🏦 Mode de paiement")
    c1, c2, c3, c4 = st.columns(4)
    mode_paiement = {
        "Chèque": c1.checkbox("Chèque", value=bool(dossier_data.get("Chèque", False))),
        "Virement": c2.checkbox("Virement", value=bool(dossier_data.get("Virement", False))),
        "Carte": c3.checkbox("Carte bancaire", value=bool(dossier_data.get("Carte bancaire", False))),
        "Venmo": c4.checkbox("Venmo", value=bool(dossier_data.get("Venmo", False))),
    }

    # --- Ligne 5 ---
    escrow = st.checkbox("💰 Escrow", value=bool(dossier_data.get("Escrow", False)))

    # --- Statut du dossier ---
    st.markdown("### 📌 Statut du dossier")
    c1, c2, c3 = st.columns(3)
    accepte = c1.checkbox("Dossier accepté", value=bool(dossier_data.get("Dossier accepté", False)))
    date_acc = c1.date_input("Date", value=pd.to_datetime(dossier_data.get("Date accepté", date.today()), errors='coerce').date() if dossier_data.get("Date accepté") else date.today())

    refuse = c2.checkbox("Dossier refusé", value=bool(dossier_data.get("Dossier refusé", False)))
    date_ref = c2.date_input("Date", value=pd.to_datetime(dossier_data.get("Date refusé", date.today()), errors='coerce').date() if dossier_data.get("Date refusé") else date.today())

    annule = c3.checkbox("Dossier annulé", value=bool(dossier_data.get("Dossier annulé", False)))
    date_ann = c3.date_input("Date", value=pd.to_datetime(dossier_data.get("Date annulé", date.today()), errors='coerce').date() if dossier_data.get("Date annulé") else date.today())

    st.markdown("### ⚠️ Autres statuts")
    c1, c2 = st.columns(2)
    rfe = c1.checkbox("RFE", value=bool(dossier_data.get("RFE", False)))
    envoi = c2.checkbox("📤 Dossier envoyé", value=bool(dossier_data.get("Dossier envoyé", False)))
    date_envoi = c2.date_input("Date d’envoi", value=pd.to_datetime(dossier_data.get("Date envoi", date.today()), errors='coerce').date() if dossier_data.get("Date envoi") else date.today())

    # --- Ligne 6 ---
    commentaires = st.text_area("📝 Commentaires", value=dossier_data.get("Commentaires", ""), height=100)

    # --- Bouton de sauvegarde ---
    if st.button("💾 Enregistrer les modifications"):
        idx = df[df["Dossier N"] == dossier_num].index
        if not idx.empty:
            i = idx[0]
            df.at[i, "Nom"] = nom_client
            df.at[i, "Date création"] = date_creation
            df.at[i, "Catégories"] = cat_sel
            df.at[i, "Sous-catégories"] = souscat_sel
            df.at[i, "Visa"] = visa_sel
            df.at[i, "Montant honoraires (US $)"] = honoraires
            df.at[i, "Date Acompte 1"] = date_acompte1
            df.at[i, "Acompte 1"] = acompte1
            df.at[i, "Escrow"] = escrow
            df.at[i, "Commentaires"] = commentaires
            df.at[i, "Dossier accepté"] = accepte
            df.at[i, "Dossier refusé"] = refuse
            df.at[i, "Dossier annulé"] = annule
            df.at[i, "Date accepté"] = date_acc
            df.at[i, "Date refusé"] = date_ref
            df.at[i, "Date annulé"] = date_ann
            df.at[i, "RFE"] = rfe
            df.at[i, "Dossier envoyé"] = envoi
            df.at[i, "Date envoi"] = date_envoi
            for m, v in mode_paiement.items():
                df.at[i, m] = v

            # 🔁 Escrow automatique
            if acompte1 > 0 and honoraires == 0:
                df.at[i, "Escrow"] = True

            st.session_state["data_xlsx"]["Clients"] = df
            save_xlsx_local(st.session_state["data_xlsx"])
            save_xlsx_to_dropbox(st.session_state["data_xlsx"])
            st.success("✅ Dossier mis à jour et sauvegardé.")

            # ✅ Réinitialisation propre
            st.session_state["reset_gestion"] = True
            st.stop()



