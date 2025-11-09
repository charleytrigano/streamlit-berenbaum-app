import streamlit as st
import pandas as pd
from datetime import date
from utils_dropbox import save_xlsx_local, save_xlsx_to_dropbox


def tab_gestion():
    """Onglet de gestion des dossiers clients."""
    st.header("📁 Gestion des dossiers")

    # Vérifier si les données Excel sont chargées
    if "data_xlsx" not in st.session_state or not st.session_state["data_xlsx"]:
        st.warning("⚠️ Aucune donnée disponible. Chargez d'abord le fichier Excel via l'onglet '📄 Fichiers'.")
        return

    data = st.session_state["data_xlsx"]
    if "Clients" not in data:
        st.error("❌ Feuille 'Clients' manquante dans le fichier Excel.")
        return

    df_clients = data["Clients"]
    if df_clients.empty:
        st.warning("📄 Aucune donnée client trouvée.")
        return

    # --- Sélection du dossier ---
    st.subheader("🔎 Sélection du dossier")

    col1, col2 = st.columns(2)
    dossiers = sorted(df_clients["Dossier N"].dropna().astype(str).unique().tolist())
    noms = sorted(df_clients["Nom"].dropna().astype(str).unique().tolist())

    dossier_sel = col1.selectbox("Dossier N", [""] + dossiers, key="gestion_sel_dossier")
    nom_sel = col2.selectbox("Nom du client", [""] + noms, key="gestion_sel_nom")

    # Synchronisation Dossier <-> Nom
    if dossier_sel:
        selected_row = df_clients[df_clients["Dossier N"].astype(str) == dossier_sel]
    elif nom_sel:
        selected_row = df_clients[df_clients["Nom"].astype(str) == nom_sel]
    else:
        selected_row = pd.DataFrame()

    if selected_row.empty:
        st.info("👉 Sélectionnez un dossier pour afficher ses informations.")
        return

    dossier_data = selected_row.iloc[0].to_dict()

    st.divider()
    st.subheader("🧾 Détails du dossier")

    # --- Ligne 1 : Dossier / Nom / Date création ---
    c1, c2, c3 = st.columns(3)
    dossier_num = c1.text_input("Dossier N", dossier_data.get("Dossier N", ""))
    nom_client = c2.text_input("Nom du client", dossier_data.get("Nom", ""))
    date_creation = c3.date_input(
        "Date (création)",
        value=pd.to_datetime(dossier_data.get("Date", date.today()), errors="coerce").date() if pd.notna(dossier_data.get("Date", None)) else date.today(),
        key="gestion_date_creation"
    )

    # --- Ligne 2 : Catégorie / Sous-catégorie / Visa ---
    c4, c5, c6 = st.columns(3)
    visa_sheet = data.get("Visa", pd.DataFrame())
    categories = sorted(visa_sheet["Catégories"].dropna().unique().tolist()) if "Catégories" in visa_sheet else []
    cat_sel = c4.selectbox("Catégorie", [""] + categories, index=([""] + categories).index(dossier_data.get("Catégories", "")) if dossier_data.get("Catégories", "") in categories else 0)

    sous_categories = []
    if not visa_sheet.empty and "Sous-catégories" in visa_sheet.columns:
        sous_categories = sorted(
            visa_sheet.loc[visa_sheet["Catégories"] == cat_sel, "Sous-catégories"].dropna().unique().tolist()
        )
    sous_cat_sel = c5.selectbox("Sous-catégorie", [""] + sous_categories, index=([""] + sous_categories).index(dossier_data.get("Sous-catégories", "")) if dossier_data.get("Sous-catégories", "") in sous_categories else 0)

    visa_list = sorted(visa_sheet.columns[2:].tolist()) if not visa_sheet.empty else []
    visa_sel = c6.selectbox("Visa", [""] + visa_list, index=([""] + visa_list).index(dossier_data.get("Visa", "")) if dossier_data.get("Visa", "") in visa_list else 0)

    # --- Ligne 3 : Montants / Acompte 1 ---
    c7, c8, c9 = st.columns(3)
    honoraires = c7.number_input("Montant honoraires (US $)", value=float(dossier_data.get("Montant honoraires (US $)", 0)) if pd.notna(dossier_data.get("Montant honoraires (US $)", None)) else 0.0)
    date_acompte1 = c8.date_input("Date Acompte 1", value=pd.to_datetime(dossier_data.get("Date Acompte 1", date.today()), errors="coerce").date() if pd.notna(dossier_data.get("Date Acompte 1", None)) else date.today())
    acompte1 = c9.number_input("Acompte 1 (US $)", value=float(dossier_data.get("Acompte 1", 0)) if pd.notna(dossier_data.get("Acompte 1", None)) else 0.0)

    # --- Ligne 4 : Mode de paiement ---
    st.markdown("💳 **Mode de paiement**")
    c10, c11, c12, c13 = st.columns(4)
    mode_cheque = c10.checkbox("Chèque", value=dossier_data.get("Mode paiement", "") == "Chèque")
    mode_virement = c11.checkbox("Virement", value=dossier_data.get("Mode paiement", "") == "Virement")
    mode_cb = c12.checkbox("Carte bancaire", value=dossier_data.get("Mode paiement", "") == "Carte bancaire")
    mode_venmo = c13.checkbox("Venmo", value=dossier_data.get("Mode paiement", "") == "Venmo")

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

    # --- Ligne 5 : Escrow ---
    escrow_auto = acompte1 > 0 and honoraires == 0
    escrow = st.checkbox("Mettre en Escrow", value=dossier_data.get("Escrow", escrow_auto))

    # --- Ligne 6 : Statut du dossier ---
    st.subheader("📂 Statut du dossier")
    c14, c15 = st.columns([1, 3])
    col_a, col_b, col_c = st.columns(3)
    acc = col_a.checkbox("✅ Dossier accepté", value=bool(dossier_data.get("Accepté", False)))
    date_acc = col_a.date_input("Date", value=pd.to_datetime(dossier_data.get("Date accepté", date.today()), errors="coerce").date() if pd.notna(dossier_data.get("Date accepté", None)) else date.today())
    ref = col_b.checkbox("❌ Dossier refusé", value=bool(dossier_data.get("Refusé", False)))
    date_ref = col_b.date_input("Date ", value=pd.to_datetime(dossier_data.get("Date refusé", date.today()), errors="coerce").date() if pd.notna(dossier_data.get("Date refusé", None)) else date.today())
    ann = col_c.checkbox("⚠️ Dossier annulé", value=bool(dossier_data.get("Annulé", False)))
    date_ann = col_c.date_input("Date  ", value=pd.to_datetime(dossier_data.get("Date annulé", date.today()), errors="coerce").date() if pd.notna(dossier_data.get("Date annulé", None)) else date.today())
    rfe = st.checkbox("📄 RFE (Requête complémentaire)", value=bool(dossier_data.get("RFE", False)))

    # --- Ligne 7 : Commentaires ---
    commentaires = st.text_area("🗒️ Commentaires", value=dossier_data.get("Commentaires", ""))

    st.divider()

    if st.button("💾 Enregistrer les modifications", use_container_width=True):
        try:
            # Mise à jour du dataframe
            idx = df_clients.index[(df_clients["Dossier N"].astype(str) == str(dossier_num)) | (df_clients["Nom"].astype(str) == str(nom_client))]
            if not idx.empty:
                i = idx[0]
                df_clients.at[i, "Dossier N"] = dossier_num
                df_clients.at[i, "Nom"] = nom_client
                df_clients.at[i, "Date"] = date_creation
                df_clients.at[i, "Catégories"] = cat_sel
                df_clients.at[i, "Sous-catégories"] = sous_cat_sel
                df_clients.at[i, "Visa"] = visa_sel
                df_clients.at[i, "Montant honoraires (US $)"] = honoraires
                df_clients.at[i, "Acompte 1"] = acompte1
                df_clients.at[i, "Date Acompte 1"] = date_acompte1
                df_clients.at[i, "Mode paiement"] = mode_paiement
                df_clients.at[i, "Escrow"] = escrow
                df_clients.at[i, "Accepté"] = acc
                df_clients.at[i, "Date accepté"] = date_acc
                df_clients.at[i, "Refusé"] = ref
                df_clients.at[i, "Date refusé"] = date_ref
                df_clients.at[i, "Annulé"] = ann
                df_clients.at[i, "Date annulé"] = date_ann
                df_clients.at[i, "RFE"] = rfe
                df_clients.at[i, "Commentaires"] = commentaires

            # --- Gestion de la feuille Escrow ---
            if escrow or (acompte1 > 0 and honoraires == 0):
                escrow_df = data.get("Escrow", pd.DataFrame(columns=["Dossier N", "Nom", "Montant", "Date envoi", "État", "Date réclamation"]))
                new_row = {
                    "Dossier N": dossier_num,
                    "Nom": nom_client,
                    "Montant": acompte1,
                    "Date envoi": date.today(),
                    "État": "En attente",
                    "Date réclamation": ""
                }
                escrow_df = pd.concat([escrow_df[escrow_df["Dossier N"] != dossier_num], pd.DataFrame([new_row])], ignore_index=True)
                data["Escrow"] = escrow_df

            # Sauvegarde
            data["Clients"] = df_clients
            save_xlsx_local(data)
            save_xlsx_to_dropbox(data)

            st.success("✅ Dossier mis à jour avec succès !")
            st.rerun()

        except Exception as e:
            st.error(f"❌ Erreur lors de la sauvegarde : {e}")
