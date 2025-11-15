import streamlit as st
import pandas as pd
from common_data import ensure_loaded, save_all, MAIN_FILE

def tab_ajouter():
    st.header("➕ Ajouter un dossier")

    data = ensure_loaded(MAIN_FILE)
    if data is None:
        st.warning("Aucun fichier chargé.")
        return

    df = data["Clients"]

    # --- AUTO-ID sécurisé ---
    valid_ids = pd.to_numeric(df["Dossier N"], errors="coerce").dropna()
    next_id = 1 if valid_ids.empty else int(valid_ids.max()) + 1

    st.write(f"**Numéro de dossier attribué automatiquement : {next_id}**")

    nom = st.text_input("Nom du client")

    col1, col2, col3 = st.columns(3)
    with col1:
        categorie = st.text_input("Catégorie")
    with col2:
        sous_cat = st.text_input("Sous-catégorie")
    with col3:
        visa = st.text_input("Visa")

    colA, colB = st.columns(2)
    with colA:
        montant = st.number_input("Montant honoraires (US $)", min_value=0.0, step=50.0)
    with colB:
        autres_frais = st.number_input("Autres frais (US $)", min_value=0.0, step=10.0)

    st.subheader("Acompte")
    colA1, colA2 = st.columns(2)
    with colA1:
        acompte1 = st.number_input("Acompte 1", min_value=0.0, step=10.0)
    with colA2:
        date_acompte1 = st.date_input("Date Acompte 1")

    escrow = st.checkbox("Mettre le dossier en Escrow")

    dossier_envoye = st.checkbox("Dossier envoyé")
    if dossier_envoye:
        date_envoye = st.date_input("Date envoi")
    else:
        date_envoye = None

    if st.button("💾 Enregistrer le dossier"):
        new_row = {
            "Dossier N": next_id,
            "Nom": nom,
            "Date": pd.Timestamp.today().normalize(),
            "Catégorie": categorie,  # assurant cohérence nom colonne
            "Sous-catégorie": sous_cat,
            "Visa": visa,
            "Montant honoraires (US $)": montant,
            "Autres frais (US $)": autres_frais,
            "Acompte 1": acompte1,
            "Date Acompte 1": pd.to_datetime(date_acompte1),
            "Acompte 2": "",
            "Date Acompte 2": "",
            "Acompte 3": "",
            "Date Acompte 3": "",
            "Acompte 4": "",
            "Date Acompte 4": "",
            "Escrow": escrow,
            "Dossier envoye": dossier_envoye,
            "Date envoi": pd.to_datetime(date_envoye) if date_envoye else pd.NaT,
            "Dossier accepte": "",
            "Dossier refuse": "",
            "Dossier annule": "",
            "RFE": "",
            "Date RFE": ""
        }

        df.loc[len(df)] = new_row
        save_all()
        st.success("Dossier ajouté avec succès !")
