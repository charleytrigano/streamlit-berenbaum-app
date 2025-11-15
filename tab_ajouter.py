import streamlit as st
import pandas as pd
from datetime import date
from common_data import ensure_loaded, save_all, CLIENTS_COLUMNS


def tab_ajouter():
    st.header("➕ Ajouter un dossier")

    data = ensure_loaded()
    if data is None:
        st.warning("Fichier non chargé — importe le fichier via l’onglet 📄 Fichiers.")
        return

    df = data["Clients"]

    # Numéro de dossier automatique (max numérique + 1)
    valid_ids = pd.to_numeric(df["Dossier N"], errors="coerce").dropna()
    next_id = 1 if valid_ids.empty else int(valid_ids.max()) + 1
    st.info(f"Numéro de dossier attribué automatiquement : **{next_id}**")

    nom = st.text_input("Nom du client")

    c1, c2, c3 = st.columns(3)
    with c1:
        categorie = st.text_input("Catégories")
    with c2:
        sous_cat = st.text_input("Sous-catégories")
    with c3:
        visa = st.text_input("Visa")

    c4, c5 = st.columns(2)
    with c4:
        montant_hono = st.number_input("Montant honoraires (US $)", min_value=0.0, step=50.0)
    with c5:
        autres_frais = st.number_input("Autres frais (US $)", min_value=0.0, step=10.0)

    st.markdown("### Acompte")
    c6, c7, c8 = st.columns([1, 1, 1])
    with c6:
        acompte1 = st.number_input("Acompte 1", min_value=0.0, step=10.0)
    with c7:
        date_acompte1 = st.date_input("Date Acompte 1", value=date.today())
    with c8:
        mode_paie = st.selectbox("mode de paiement", ["", "Chèque", "Virement", "Carte bancaire", "Venmo"])

    escrow_manual = st.checkbox("Escrow")

    commentaires = st.text_area("Commentaires")

    if st.button("💾 Enregistrer le dossier"):
        if not nom.strip():
            st.warning("Le nom du client est obligatoire.")
            return

        # Date de création = aujourd'hui
        today = pd.Timestamp(date.today())

        new_row = {
            "Dossier N": next_id,
            "Nom": nom.strip(),
            "Date": today,
            "Catégories": categorie.strip(),
            "Sous-catégories": sous_cat.strip(),
            "Visa": visa.strip(),
            "Montant honoraires (US $)": float(montant_hono),
            "Autres frais (US $)": float(autres_frais),
            "Acompte 1": float(acompte1),
            "Date Acompte 1": pd.to_datetime(date_acompte1),
            "mode de paiement": mode_paie,
            # Escrow sera recalculé automatiquement ensuite, mais on stocke aussi la valeur manuelle
            "Escrow": escrow_manual,
            "Acompte 2": 0.0,
            "Date Acompte 2": pd.NaT,
            "Acompte 3": 0.0,
            "Date Acompte 3": pd.NaT,
            "Acompte 4": 0.0,
            "Date Acompte 4": pd.NaT,
            "Dossier envoyé": False,
            "Date envoi": pd.NaT,
            "Dossier accepté": False,
            "Date acceptation": pd.NaT,
            "Dossier refusé": False,
            "Date refus": pd.NaT,
            "Dossier Annulé": False,
            "Date annulation": pd.NaT,
            "RFE": False,
            "Commentaires": commentaires,
        }

        # On s'assure d'avoir toutes les colonnes
        for col in CLIENTS_COLUMNS:
            if col not in new_row:
                new_row[col] = pd.NA

        data["Clients"] = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        st.session_state["data_xlsx"] = data

        save_all()
        st.success(f"Dossier {next_id} ajouté.")
