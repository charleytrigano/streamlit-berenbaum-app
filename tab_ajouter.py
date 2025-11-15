import streamlit as st
import pandas as pd
from common_data import ensure_loaded, save_all

def tab_ajouter():
    st.header("➕ Ajouter un dossier")

    data = ensure_loaded()
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
        categorie = st.text_input("Catégories")
    with col2:
        sous_cat = st.text_input("Sous-catégories")
    with col3:
        visa = st.text_input("Visa")

    # Montant Honoraires et Autres Frais (cols fines) + Total
    colA, colB, colC = st.columns([1, 1, 1])
    with colA:
        montant = st.number_input("Montant honoraires (US $)", min_value=0.0, step=50.0, format="%.2f")
    with colB:
        autres_frais = st.number_input("Autres frais (US $)", min_value=0.0, step=10.0, format="%.2f")
    with colC:
        total_facture = montant + autres_frais
        st.metric("Total facturé (US $)", f"{total_facture:,.2f}")

    # Modes de paiement sur une ligne
    st.subheader("Mode de paiement")
    pm_cols = st.columns(4)
    with pm_cols[0]:
        pm_cheque = st.checkbox("Chèque")
    with pm_cols[1]:
        pm_cb = st.checkbox("CB")
    with pm_cols[2]:
        pm_vir = st.checkbox("Virement")
    with pm_cols[3]:
        pm_venmo = st.checkbox("Venmo")

    mode_paiement = []
    if pm_cheque: mode_paiement.append("Chèque")
    if pm_cb: mode_paiement.append("CB")
    if pm_vir: mode_paiement.append("Virement")
    if pm_venmo: mode_paiement.append("Venmo")
    mode_paiement_str = ", ".join(mode_paiement)

    st.subheader("Acompte")
    colA1, colA2 = st.columns(2)
    with colA1:
        acompte1 = st.number_input("Acompte 1", min_value=0.0, step=10.0)
    with colA2:
        date_acompte1 = st.date_input("Date Acompte 1")

    escrow = st.checkbox("Mettre le dossier en Escrow")
    commentaires = st.text_area("Commentaires")

    # ---------- Tableau des dossiers existants avec filtres ----------
    st.subheader("Liste des dossiers existants")
    # Filtres basiques
    df_filtered = df.copy()
    filt_cols = st.columns(4)
    with filt_cols[0]:
        nom_filtre = st.text_input("Filtrer par nom", "")
        if nom_filtre:
            df_filtered = df_filtered[df_filtered["Nom"].str.lower().str.contains(nom_filtre.lower())]
    with filt_cols[1]:
        cat_filtre = st.text_input("Filtrer par catégories", "")
        if cat_filtre:
            df_filtered = df_filtered[df_filtered["Catégories"].str.lower().str.contains(cat_filtre.lower())]
    with filt_cols[2]:
        visa_filtre = st.text_input("Filtrer par visa", "")
        if visa_filtre:
            df_filtered = df_filtered[df_filtered["Visa"].str.lower().str.contains(visa_filtre.lower())]
    with filt_cols[3]:
        montant_min = st.number_input("Montant min facturé", min_value=0.0, value=0.0)
        df_filtered = df_filtered[df_filtered["Montant honoraires (US $)"] >= montant_min]

    # Affichage tableau résumé
    display_cols = [
        "Dossier N", "Nom", "Catégories", "Sous-catégories", "Visa",
        "Montant honoraires (US $)", "Autres frais (US $)", "Total facture",
        "Acompte 1", "Date Acompte 1", "mode de paiement", "Escrow", "Commentaires"
    ]
    existing_cols = [c for c in display_cols if c in df_filtered.columns]
    st.dataframe(df_filtered[existing_cols], use_container_width=True)

    # ---------- Enregistrement dossier ----------
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
            "Total facture": total_facture,
            "Acompte 1": acompte1,
            "Date Acompte 1": pd.to_datetime(date_acompte1) if date_acompte1 else pd.NaT,
            "mode de paiement": mode_paiement_str,
            "Escrow": escrow,
            "Acompte 2": "",
            "Date Acompte 2": "",
            "Acompte 3": "",
            "Date Acompte 3": "",
            "Acompte 4": "",
            "Date Acompte 4": "",
            "Commentaires": commentaires,
        }

        df.loc[len(df)] = new_row
        save_all()
        st.success("Dossier ajouté avec succès !")
