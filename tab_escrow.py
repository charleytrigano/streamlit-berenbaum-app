import streamlit as st
import pandas as pd
import io
import dropbox


def tab_escrow():
    """Onglet Escrow - gestion des acomptes en attente et réclamations."""
    st.header("🛡️ Gestion Escrow")

    # Vérifie si les données Excel sont chargées
    if "data_xlsx" not in st.session_state or not st.session_state["data_xlsx"]:
        st.warning("⚠️ Aucune donnée chargée. Chargez d'abord le fichier Excel via '📄 Fichiers'.")
        return

    data = st.session_state["data_xlsx"]

    # Vérifie la présence de la feuille Escrow
    if "Escrow" not in data:
        st.error("❌ Feuille 'Escrow' manquante dans le fichier Excel.")
        return

    df_escrow = data["Escrow"].copy()

    st.markdown("### 💰 Dossiers Escrow enregistrés")

    if df_escrow.empty:
        st.info("Aucun dossier dans Escrow.")
    else:
        st.dataframe(df_escrow, use_container_width=True, height=350)

    st.markdown("---")
    st.subheader("➕ Ajouter un dossier à Escrow")

    # Formulaire d’ajout Escrow avec clés uniques
    dossier = st.text_input("Numéro de dossier", key="escrow_dossier_add")
    nom = st.text_input("Nom du client", key="escrow_nom_add")
    montant = st.number_input("Montant Acompte (US $)", min_value=0.0, step=50.0, key="escrow_montant_add")
    date_envoi = st.date_input("Date d’envoi en Escrow", key="escrow_date_envoi_add")
    commentaire = st.text_area("Commentaires", key="escrow_comment_add")

    st.markdown("### ⚙️ Gestion du statut")

    reclamation = st.checkbox("Dossier réclamé ?", key="escrow_reclamation_add")
    date_reclamation = st.date_input("Date de réclamation (si applicable)", key="escrow_date_recl_add")

    if st.button("💾 Enregistrer dans Escrow", key="escrow_save_btn"):
        new_row = {
            "Dossier N": dossier,
            "Nom": nom,
            "Montant": montant,
            "Date envoi": date_envoi,
            "État": "Réclamé" if reclamation else "En attente",
            "Date réclamation": date_reclamation if reclamation else "",
            "Commentaires": commentaire,
        }

        df_escrow = pd.concat([df_escrow, pd.DataFrame([new_row])], ignore_index=True)
        st.session_state["data_xlsx"]["Escrow"] = df_escrow

        # Sauvegarde sur Dropbox
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
            st.success("✅ Dossier ajouté et fichier sauvegardé sur Dropbox.")
        except Exception as e:
            st.warning(f"⚠️ Sauvegarde Dropbox échouée : {e}")

    st.markdown("---")
    st.subheader("🔄 Marquer un dossier comme réclamé")

    num_recl = st.text_input("Numéro du dossier à marquer", key="escrow_mark_num")
    if st.button("📬 Marquer comme réclamé", key="escrow_mark_btn"):
        if num_recl and num_recl in df_escrow["Dossier N"].astype(str).values:
            df_escrow.loc[df_escrow["Dossier N"].astype(str) == num_recl, "État"] = "Réclamé"
            df_escrow.loc[df_escrow["Dossier N"].astype(str) == num_recl, "Date réclamation"] = pd.Timestamp.now().date()
            st.session_state["data_xlsx"]["Escrow"] = df_escrow

            # Sauvegarde automatique
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
                st.success(f"📩 Dossier {num_recl} marqué comme réclamé et sauvegardé.")
            except Exception as e:
                st.warning(f"⚠️ Sauvegarde Dropbox échouée : {e}")
        else:
            st.warning("Numéro de dossier introuvable dans Escrow.")

    st.markdown("---")
    st.subheader("📤 Télécharger Escrow")

    if st.button("Générer fichier Escrow", key="escrow_dl_btn"):
        with io.BytesIO() as buffer:
            df_escrow.to_excel(buffer, index=False, sheet_name="Escrow")
            buffer.seek(0)
            st.download_button(
                label="💾 Télécharger Escrow.xlsx",
                data=buffer,
                file_name="Escrow.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="escrow_dl_button"
            )
