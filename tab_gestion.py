import streamlit as st
import pandas as pd
from datetime import date
from utils_gdrive_oauth import upload_to_drive, download_from_drive

# ============================
#   FONCTION PRINCIPALE
# ============================

def tab_gestion():
    st.title("📁 Gestion des dossiers")

    # Charger les données Excel depuis Google Drive
    if "data_xlsx" not in st.session_state:
        data = download_from_drive("Clients BL.xlsx")
        if data:
            st.session_state["data_xlsx"] = data
        else:
            st.error("⚠️ Impossible de charger le fichier Clients BL.xlsx depuis Google Drive.")
            return

    df_clients = st.session_state["data_xlsx"].get("Clients", pd.DataFrame())
    df_visa = st.session_state["data_xlsx"].get("Visa", pd.DataFrame())
    df_escrow = st.session_state["data_xlsx"].get("Escrow", pd.DataFrame())

    # ======================
    #   Sélection dossier
    # ======================

    st.subheader("🔍 Sélection d’un dossier")

    col1, col2 = st.columns(2)
    dossier_n_sel = col1.selectbox(
        "Choisir par Dossier N°",
        options=[""] + sorted(df_clients["Dossier N"].astype(str).unique().tolist()),
        key="gestion_dossier_num"
    )

    nom_sel = col2.selectbox(
        "Ou choisir par Nom",
        options=[""] + sorted(df_clients["Nom"].astype(str).unique().tolist()),
        key="gestion_nom"
    )

    dossier_data = pd.Series(dtype=object)
    if dossier_n_sel:
        dossier_data = df_clients[df_clients["Dossier N"].astype(str) == str(dossier_n_sel)].iloc[0]
    elif nom_sel:
        dossier_data = df_clients[df_clients["Nom"].astype(str) == str(nom_sel)].iloc[0]

    if dossier_data.empty:
        st.info("👈 Sélectionne un dossier pour afficher et modifier ses informations.")
        return

    st.divider()
    st.subheader("🗂️ Informations générales")

    # ======================
    #   Informations générales
    # ======================

    c1, c2, c3 = st.columns(3)
    dossier_n = c1.text_input("Dossier N°", dossier_data.get("Dossier N", ""))
    nom = c2.text_input("Nom du client", dossier_data.get("Nom", ""))
    date_creation = c3.date_input(
        "Date (création)",
        value=pd.to_datetime(dossier_data.get("Date", date.today())).date() if pd.notna(dossier_data.get("Date", None)) else date.today()
    )

    st.divider()

    st.subheader("🏷️ Classification et Visa")

    cats = [c for c in df_visa.columns if c not in ["Catégories", "Sous-catégories", "Visa"]]
    categories = df_visa["Catégories"].dropna().unique().tolist() if "Catégories" in df_visa else []
    sous_cats = df_visa["Sous-catégories"].dropna().unique().tolist() if "Sous-catégories" in df_visa else []
    visas = df_visa["Visa"].dropna().unique().tolist() if "Visa" in df_visa else []

    c4, c5, c6 = st.columns(3)
    cat_sel = c4.selectbox("Catégorie", [""] + categories, index=([""] + categories).index(dossier_data.get("Catégories", "")) if dossier_data.get("Catégories", "") in categories else 0)
    sous_cat_sel = c5.selectbox("Sous-catégorie", [""] + sous_cats, index=([""] + sous_cats).index(dossier_data.get("Sous-catégories", "")) if dossier_data.get("Sous-catégories", "") in sous_cats else 0)
    visa_sel = c6.selectbox("Visa", [""] + visas, index=([""] + visas).index(dossier_data.get("Visa", "")) if dossier_data.get("Visa", "") in visas else 0)

    st.divider()

    # ======================
    #   Paiements & Escrow
    # ======================

    st.subheader("💵 Paiements et acompte")

    c1, c2, c3 = st.columns(3)
    montant_hono = c1.number_input("Montant honoraires (US $)", value=float(dossier_data.get("Montant honoraires (US $)", 0)))
    acompte1_date = c2.date_input("Date acompte 1", value=pd.to_datetime(dossier_data.get("Date Acompte 1", date.today())).date() if pd.notna(dossier_data.get("Date Acompte 1", None)) else date.today())
    acompte1 = c3.number_input("Acompte 1 (US $)", value=float(dossier_data.get("Acompte 1", 0)))

    c4, c5, c6, c7 = st.columns(4)
    mode_cheque = c4.checkbox("Chèque", value=(dossier_data.get("Mode de paiement") == "Chèque"))
    mode_virement = c5.checkbox("Virement", value=(dossier_data.get("Mode de paiement") == "Virement"))
    mode_cb = c6.checkbox("Carte bancaire", value=(dossier_data.get("Mode de paiement") == "Carte bancaire"))
    mode_venmo = c7.checkbox("Venmo", value=(dossier_data.get("Mode de paiement") == "Venmo"))

    if mode_cheque:
        mode_paiement = "Chèque"
    elif mode_virement:
        mode_paiement = "Virement"
    elif mode_cb:
        mode_paiement = "Carte bancaire"
    elif mode_venmo:
        mode_paiement = "Venmo"
    else:
        mode_paiement = ""

    escrow_checked = st.checkbox("Escrow", value=bool(dossier_data.get("Escrow", False)))

    st.divider()

    # ======================
    #   Statut du dossier
    # ======================

    st.subheader("📌 Statut du dossier")

    c1, c2 = st.columns([1, 1])
    dossier_envoye = c1.checkbox("Dossier envoyé", value=bool(dossier_data.get("Dossier envoyé", False)))
    date_envoye = c2.date_input("Date envoi", value=pd.to_datetime(dossier_data.get("Date envoi", date.today())).date() if pd.notna(dossier_data.get("Date envoi", None)) else date.today())

    c3, c4 = st.columns(2)
    dossier_accepte = c3.checkbox("Dossier accepté", value=bool(dossier_data.get("Dossier accepté", False)))
    date_accepte = c4.date_input("Date acceptation", value=pd.to_datetime(dossier_data.get("Date acceptation", date.today())).date() if pd.notna(dossier_data.get("Date acceptation", None)) else date.today())

    c5, c6 = st.columns(2)
    dossier_refuse = c5.checkbox("Dossier refusé", value=bool(dossier_data.get("Dossier refusé", False)))
    date_refuse = c6.date_input("Date refus", value=pd.to_datetime(dossier_data.get("Date refus", date.today())).date() if pd.notna(dossier_data.get("Date refus", None)) else date.today())

    c7, c8 = st.columns(2)
    dossier_annule = c7.checkbox("Dossier annulé", value=bool(dossier_data.get("Dossier annulé", False)))
    date_annule = c8.date_input("Date annulation", value=pd.to_datetime(dossier_data.get("Date annulation", date.today())).date() if pd.notna(dossier_data.get("Date annulation", None)) else date.today())

    rfe = st.checkbox("RFE obligatoire", value=bool(dossier_data.get("RFE", False)))

    st.divider()

    # ======================
    #   Commentaires
    # ======================
    commentaires = st.text_area("Commentaires", value=dossier_data.get("Commentaires", ""), height=100)

    # ======================
    #   Enregistrement
    # ======================

    if st.button("💾 Enregistrer les modifications"):

        try:
            idx = df_clients[df_clients["Dossier N"] == dossier_data["Dossier N"]].index[0]
            df_clients.loc[idx, "Nom"] = nom
            df_clients.loc[idx, "Date"] = date_creation
            df_clients.loc[idx, "Catégories"] = cat_sel
            df_clients.loc[idx, "Sous-catégories"] = sous_cat_sel
            df_clients.loc[idx, "Visa"] = visa_sel
            df_clients.loc[idx, "Montant honoraires (US $)"] = montant_hono
            df_clients.loc[idx, "Acompte 1"] = acompte1
            df_clients.loc[idx, "Date Acompte 1"] = acompte1_date
            df_clients.loc[idx, "Mode de paiement"] = mode_paiement
            df_clients.loc[idx, "Escrow"] = escrow_checked
            df_clients.loc[idx, "Commentaires"] = commentaires

            df_clients.loc[idx, "Dossier envoyé"] = dossier_envoye
            df_clients.loc[idx, "Date envoi"] = date_envoye
            df_clients.loc[idx, "Dossier accepté"] = dossier_accepte
            df_clients.loc[idx, "Date acceptation"] = date_accepte
            df_clients.loc[idx, "Dossier refusé"] = dossier_refuse
            df_clients.loc[idx, "Date refus"] = date_refuse
            df_clients.loc[idx, "Dossier annulé"] = dossier_annule
            df_clients.loc[idx, "Date annulation"] = date_annule
            df_clients.loc[idx, "RFE"] = rfe

            # Escrow automatique si acompte sans honoraires
            if acompte1 > 0 and montant_hono == 0:
                escrow_checked = True
                if "Escrow" in st.session_state["data_xlsx"]:
                    df_escrow = st.session_state["data_xlsx"]["Escrow"]
                else:
                    df_escrow = pd.DataFrame(columns=["Dossier N", "Nom", "Montant", "Date envoi", "Etat", "Date réclamation"])
                if dossier_n not in df_escrow["Dossier N"].astype(str).values:
                    new_row = pd.DataFrame({
                        "Dossier N": [dossier_n],
                        "Nom": [nom],
                        "Montant": [acompte1],
                        "Date envoi": [date_envoye],
                        "Etat": ["En attente"],
                        "Date réclamation": [""]
                    })
                    df_escrow = pd.concat([df_escrow, new_row], ignore_index=True)
                    st.session_state["data_xlsx"]["Escrow"] = df_escrow

            st.session_state["data_xlsx"]["Clients"] = df_clients

            upload_to_drive(st.session_state["data_xlsx"], "Clients BL.xlsx")

            st.success("✅ Dossier mis à jour et synchronisé sur Google Drive.")
            st.rerun()

        except Exception as e:
            st.error(f"❌ Erreur lors de l’enregistrement : {e}")
