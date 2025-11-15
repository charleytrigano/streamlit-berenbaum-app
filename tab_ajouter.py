import streamlit as st
import pandas as pd
from common_data import ensure_loaded, save_all, MAIN_FILE

def tab_ajouter():
    st.header("➕ Ajouter un dossier")

    data = ensure_loaded()  # correction: RETIRE L'ARGUMENT

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
        categorie = st.text_input("Catégories")  # correction
    with col2:
        sous_cat = st.text_input("Sous-catégories")  # correction
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

    mode_paiement = st.text_input("mode de paiement")  # nouvelle colonne (si souhaité/réel)

    escrow = st.checkbox("Mettre le dossier en Escrow")

    dossier_envoye = st.checkbox("Dossier envoyé")
    if dossier_envoye:
        date_envoye = st.date_input("Date envoi")
    else:
        date_envoye = None

    dossier_accepte = st.checkbox("Dossier accepté")
    if dossier_accepte:
        date_acceptation = st.date_input("Date acceptation")
    else:
        date_acceptation = None

    dossier_refuse = st.checkbox("Dossier refusé")
    if dossier_refuse:
        date_refus = st.date_input("Date refus")
    else:
        date_refus = None

    dossier_annule = st.checkbox("Dossier Annulé")
    if dossier_annule:
        date_annulation = st.date_input("Date annulation")
    else:
        date_annulation = None

    rfe = st.text_input("RFE")
    commentaires = st.text_area("Commentaires")

    if st.button("💾 Enregistrer le dossier"):
        new_row = {
            "Dossier N": next_id,
            "Nom": nom,
            "Date": pd.Timestamp.today().normalize(),
            "Catégories": categorie,
            "Sous-catégories": sous_cat,
            "Visa": visa,
            "Montant honoraires (US $)": montant,
            "Autres frais (US $)": autres_frais,
            "Acompte 1": acompte1,
            "Date Acompte 1": pd.to_datetime(date_acompte1) if date_acompte1 else pd.NaT,
            "mode de paiement": mode_paiement,
            "Escrow": escrow,
            "Acompte 2": "",  # à remplir selon UI, ici vide
            "Date Acompte 2": "",
            "Acompte 3": "",
            "Date Acompte 3": "",
            "Acompte 4": "",
            "Date Acompte 4": "",
            "Dossier envoyé": dossier_envoye,
            "Date envoi": pd.to_datetime(date_envoye) if date_envoye else pd.NaT,
            "Dossier accepté": dossier_accepte,
            "Date acceptation": pd.to_datetime(date_acceptation) if date_acceptation else pd.NaT,
            "Dossier refusé": dossier_refuse,
            "Date refus": pd.to_datetime(date_refus) if date_refus else pd.NaT,
            "Dossier Annulé": dossier_annule,
            "Date annulation": pd.to_datetime(date_annulation) if date_annulation else pd.NaT,
            "RFE": rfe,
            "Commentaires": commentaires,
        }

        df.loc[len(df)] = new_row
        save_all()
        st.success("Dossier ajouté avec succès !")
