import streamlit as st
import pandas as pd
import io
import dropbox

def tab_ajouter():
    """Onglet AJOUTER — ajout d’un dossier avec sauvegarde automatique Dropbox."""
    st.header("➕ Ajouter un dossier")

    # Vérifier que les données Excel sont disponibles
    if "data_xlsx" not in st.session_state or not st.session_state["data_xlsx"]:
        st.warning("⚠️ Aucune donnée chargée. Chargez d'abord votre fichier Excel via l'onglet '📄 Fichiers'.")
        return

    data = st.session_state["data_xlsx"]

    # Vérifier la présence des feuilles nécessaires
    if "Clients" not in data or "Visa" not in data:
        st.error("❌ Feuille 'Clients' ou 'Visa' manquante dans le fichier Excel.")
        return

    df_clients = data["Clients"]
    df_visa = data["Visa"]

    # === Préparation des listes pour les sélecteurs ===
    categories = df_visa.columns[1:].tolist() if not df_visa.empty else []
    selected_categorie = st.selectbox("Catégorie", [""] + categories)

    sous_categories = []
    if selected_categorie:
        sous_categories = df_visa.loc[df_visa[selected_categorie] == 1, "Sous-catégorie"].dropna().tolist()

    selected_sous_categorie = st.selectbox("Sous-catégorie", [""] + sous_categories)

    visas = df_visa["Visa"].dropna().unique().tolist() if "Visa" in df_visa.columns else []
    selected_visa = st.selectbox("Visa", [""] + visas)

    # === Champs principaux ===
    dossier = st.text_input("Numéro de dossier")
    nom = st.text_input("Nom du client")
    date_creation = st.date_input("Date de création du dossier")

    montant_honoraires = st.number_input("Montant honoraires (US $)", min_value=0.0, step=100.0)
    acompte_1 = st.number_input("Acompte 1", min_value=0.0, step=50.0)
    date_acompte_1 = st.date_input("Date Acompte 1")

    # === Mode de paiement ===
    st.markdown("**Mode de paiement :**")
    col1, col2, col3, col4 = st.columns(4)
    mode_paiement = None
    if col1.checkbox("Chèque"):
        mode_paiement = "Chèque"
    elif col2.checkbox("Virement"):
        mode_paiement = "Virement"
    elif col3.checkbox("Carte bancaire"):
        mode_paiement = "Carte bancaire"
    elif col4.checkbox("Venmo"):
        mode_paiement = "Venmo"

    # === Escrow et commentaires ===
    escrow = st.checkbox("Escrow (Acompte envoyé sans honoraires)")
    commentaires = st.text_area("Commentaires")

    st.markdown("---")

    # === Enregistrement ===
    if st.button("💾 Enregistrer le dossier"):
        new_row = {
            "Dossier N": dossier,
            "Nom": nom,
            "Date": date_creation,
            "Catégorie": selected_categorie,
            "Sous-catégorie": selected_sous_categorie,
            "Visa": selected_visa,
            "Montant honoraires (US $)": montant_honoraires,
            "Acompte 1": acompte_1,
            "Date Acompte 1": date_acompte_1,
            "Mode de paiement": mode_paiement,
            "Escrow": "Oui" if escrow else "Non",
            "Commentaires": commentaires,
        }

        df_clients = pd.concat([df_clients, pd.DataFrame([new_row])], ignore_index=True)
        st.session_state["data_xlsx"]["Clients"] = df_clients

        # === Sauvegarde locale temporaire ===
        with io.BytesIO() as buffer:
            with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                for sheet, df in st.session_state["data_xlsx"].items():
                    df.to_excel(writer, index=False, sheet_name=sheet)
            buffer.seek(0)

            # === Sauvegarde sur Dropbox ===
            try:
                token = st.secrets["DROPBOX_TOKEN"]
                folder = st.secrets.get("DROPBOX_FOLDER", "/")
                dbx = dropbox.Dropbox(token)

                dropbox_path = f"{folder}/Clients BL.xlsx"
                dbx.files_upload(buffer.read(), dropbox_path, mode=dropbox.files.WriteMode("overwrite"))
                st.success("☁️ Données sauvegardées automatiquement sur Dropbox.")
            except Exception as e:
                st.warning(f"⚠️ Sauvegarde Dropbox échouée : {e}")

    # === Téléchargement manuel ===
    st.markdown("### 📥 Télécharger une copie du fichier Excel")
    if st.button("Générer et télécharger"):
        with io.BytesIO() as buffer:
            with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                for sheet, df in st.session_state["data_xlsx"].items():
                    df.to_excel(writer, index=False, sheet_name=sheet)
            buffer.seek(0)
            st.download_button(
                label="💾 Télécharger Clients BL.xlsx",
                data=buffer,
                file_name="Clients BL.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
