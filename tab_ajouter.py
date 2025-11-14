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

    # --- ID automatique robuste ---
    ids = pd.to_numeric(df["Dossier N"], errors="coerce").dropna()

    if ids.empty:
        next_id = 1
    else:
        next_id = int(ids.max()) + 1

    st.info(f"**Numéro de dossier attribué automatiquement : {next_id}**")

    # Champs base
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

    if st.button("💾 Enregistrer le dossier"):
        new_row = {
            "Dossier N": next_id,
            "Nom": nom,
            "Date": pd.Timestamp.today().normalize(),
            "Categories": categorie,
            "Sous-categorie": sous_cat,
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
            "Escrow": "Oui" if escrow else "Non",
            "Dossier envoye": "",
            "Dossier accepte": "",
            "Dossier refuse": "",
            "Dossier annule": "",
            "RFE": "",
            "Date RFE": "",
        }

        data["Clients"] = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

        if save_all():
            st.success("✅ Dossier enregistré avec succès !")
        else:
            st.error("❌ Erreur lors de la sauvegarde.")
