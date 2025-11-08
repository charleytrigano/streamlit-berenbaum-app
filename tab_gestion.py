import streamlit as st
import pandas as pd
import io
import dropbox
from datetime import date

def tab_gestion():
    """Onglet Gestion — modification ou suppression des dossiers clients, et gestion automatique des Escrow."""

    st.header("✏️ / 🗑️ Gestion des dossiers")

    # Vérification du chargement des données
    if "data_xlsx" not in st.session_state or not st.session_state["data_xlsx"]:
        st.warning("⚠️ Aucune donnée disponible. Chargez d'abord le fichier Excel via l'onglet 📄 Fichiers.")
        return

    data = st.session_state["data_xlsx"]

    if "Clients" not in data:
        st.error("❌ Feuille 'Clients' manquante dans le fichier Excel.")
        return

    df_clients = data["Clients"].copy()
    df_escrow = data.get("Escrow", pd.DataFrame(columns=["Dossier N", "Nom", "Montant", "Date envoi", "État", "Date réclamation", "Commentaires"]))

    if df_clients.empty:
        st.info("Aucun dossier client enregistré.")
        return

    # Sélection du dossier à modifier/supprimer
    dossier_list = df_clients["Dossier N"].astype(str).tolist()
    selected_dossier = st.selectbox("Sélectionnez un dossier :", options=[""] + dossier_list, key="gestion_dossier_select")

    if not selected_dossier:
        st.stop()

    dossier_data = df_clients[df_clients["Dossier N"].astype(str) == selected_dossier].iloc[0].copy()

    st.markdown("### 🔧 Modifier le dossier sélectionné")

    # Récupération et nettoyage de la date
    raw_date = dossier_data.get("Date Acompte 1", "")
    try:
        date_parsed = pd.to_datetime(raw_date).date() if pd.notna(raw_date) else date.today()
    except Exception:
        date_parsed = date.today()

    # Formulaire de modification
    nom = st.text_input("Nom du client", value=dossier_data.get("Nom", ""), key="gestion_nom")
    montant = st.number_input("Montant honoraires (US $)", min_value=0.0, value=float(dossier_data.get("Montant honoraires (US $)", 0)), step=50.0, key="gestion_montant")
    acompte = st.number_input("Acompte 1", min_value=0.0, value=float(dossier_data.get("Acompte 1", 0)), step=50.0, key="gestion_acompte")
    date_acompte = st.date_input("Date Acompte 1", value=date_parsed, key="gestion_date_acompte")
    escrow = st.checkbox("Escrow ?", value=bool(dossier_data.get("Escrow", False)), key="gestion_escrow")
    commentaire = st.text_area("Commentaires", value=dossier_data.get("Commentaires", ""), key="gestion_commentaire")

    st.markdown("---")
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("💾 Enregistrer les modifications", key="gestion_save_btn"):
            # Mise à jour du dossier
            idx = df_clients.index[df_clients["Dossier N"].astype(str) == selected_dossier][0]
            df_clients.at[idx, "Nom"] = nom
            df_clients.at[idx, "Montant honoraires (US $)"] = montant
            df_clients.at[idx, "Acompte 1"] = acompte
            df_clients.at[idx, "Date Acompte 1"] = date_acompte
            df_clients.at[idx, "Escrow"] = escrow
            df_clients.at[idx, "Commentaires"] = commentaire

            # Gestion automatique Escrow
            if escrow or (acompte > 0 and montant == 0):
                new_row = {
                    "Dossier N": selected_dossier,
                    "Nom": nom,
                    "Montant": acompte,
                    "Date envoi": date_acompte,
                    "État": "En attente",
                    "Date réclamation": "",
                    "Commentaires": commentaire,
                }
                df_escrow = pd.concat([df_escrow, pd.DataFrame([new_row])], ignore_index=True)
                st.success("✅ Dossier ajouté automatiquement dans Escrow.")
            else:
                st.info("Aucun ajout Escrow requis.")

            st.session_state["data_xlsx"]["Clients"] = df_clients
            st.session_state["data_xlsx"]["Escrow"] = df_escrow

            st.success("💾 Modifications enregistrées localement.")

            # Proposition de sauvegarde
            save_mode = st.radio("Choisissez où sauvegarder :", ["💻 Local", "☁️ Dropbox"], horizontal=True, key="gestion_save_choice")

            if save_mode == "💻 Local":
                with io.BytesIO() as buffer:
                    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                        for sheet, df in st.session_state["data_xlsx"].items():
                            df.to_excel(writer, index=False, sheet_name=sheet)
                    buffer.seek(0)
                    st.download_button("⬇️ Télécharger le fichier Excel mis à jour", buffer, "Clients BL.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key="gestion_dl_btn")

            elif save_mode == "☁️ Dropbox":
                try:
                    token = st.secrets["DROPBOX_TOKEN"]
                    folder = st.secrets.get("DROPBOX_FOLDER", "/")
                    dbx = dropbox.Dropbox(token)

                    with io.BytesIO() as buffer:
                        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                            for sheet, df in st.session_state["data_xlsx"].items():
                                df.to_excel(writer, index=False, sheet_name=sheet)
                        buffer.seek(0)
                        dbx.files_upload(buffer.read(), f"{folder}/Clients BL.xlsx", mode=dropbox.files.WriteMode("overwrite"))

                    st.success("✅ Fichier sauvegardé sur Dropbox.")
                except Exception as e:
                    st.warning(f"⚠️ Sauvegarde Dropbox échouée : {e}")

    with col2:
        if st.button("🗑️ Supprimer le dossier", key="gestion_delete_btn"):
            df_clients = df_clients[df_clients["Dossier N"].astype(str) != selected_dossier]
            st.session_state["data_xlsx"]["Clients"] = df_clients
            st.success(f"🗑️ Dossier {selected_dossier} supprimé.")
            st.experimental_rerun()

    with col3:
        st.info("💡 Les sauvegardes peuvent être faites localement ou sur Dropbox.")
