import streamlit as st
import pandas as pd
from common_data import ensure_loaded, save_all, MAIN_FILE


def tab_gestion():
    st.header("✏️ / 🗑️ Gestion des dossiers")

    data = ensure_loaded(MAIN_FILE)
    if data is None:
        st.warning("Aucun fichier chargé.")
        return

    df = data["Clients"]

    if df.empty:
        st.info("Aucun dossier dans la feuille Clients.")
        return

    # Sélection du dossier
    dossier_ids = df["Dossier N"].astype(str).tolist()
    dossier_select = st.selectbox("Choisir un dossier", dossier_ids)

    try:
        index = df.index[df["Dossier N"].astype(str) == dossier_select][0]
    except:
        st.error("Erreur: Dossier introuvable.")
        return

    dossier = df.loc[index]

    st.subheader(f"Dossier n° {dossier['Dossier N']} — {dossier['Nom']}")

    # --- Nom ---
    nom = st.text_input("Nom", value=str(dossier["Nom"]))

    # --- Ligne Catégorie / Sous-catégorie / Visa ---
    c1, c2, c3 = st.columns(3)
    categorie = c1.text_input("Catégorie", value=str(dossier["Categories"]))
    sous_cat = c2.text_input("Sous-catégorie", value=str(dossier["Sous-categorie"]))
    visa = c3.text_input("Visa", value=str(dossier["Visa"]))

    # --- Montants ---
    c4, c5 = st.columns(2)
    montant = c4.number_input(
        "Montant honoraires (US $)",
        value=float(dossier["Montant honoraires (US $)"] or 0),
        min_value=0.0,
    )
    autres_frais = c5.number_input(
        "Autres frais (US $)",
        value=float(dossier["Autres frais (US $)"] or 0),
        min_value=0.0,
    )

    # --- Acomptes ---
    st.subheader("Acomptes")

    for n in range(1, 5):
        colA, colB, colC = st.columns([1, 1, 1.2])
        acompte_key = f"Acompte {n}"
        date_key = f"Date Acompte {n}"
        mode_key = f"Mode Paiement {n}"

        acompte_val = dossier.get(acompte_key, 0) or 0
        date_val = dossier.get(date_key, pd.NaT)
        mode_val = dossier.get(mode_key, "")

        with colA:
            new_acompte = st.number_input(acompte_key, value=float(acompte_val), min_value=0.0)
        with colB:
            new_date = st.date_input(date_key, value=date_val if pd.notna(date_val) else pd.to_datetime("today"))
        with colC:
            new_mode = st.text_input(mode_key, value=str(mode_val))

        df.loc[index, acompte_key] = new_acompte
        df.loc[index, date_key] = pd.to_datetime(new_date)
        df.loc[index, mode_key] = new_mode

    # --- ESCROW ---
    st.subheader("Escrow")

    escrow_val = bool(dossier.get("Escrow", False))
    new_escrow = st.checkbox("Mettre en Escrow", value=escrow_val)
    df.loc[index, "Escrow"] = new_escrow

    # --- STATUTS ---
    st.subheader("Statuts du dossier")

    statuses = [
        ("Dossier envoye", "Date Envoi"),
        ("Dossier accepte", "Date Acceptation"),
        ("Dossier refuse", "Date Refus"),
        ("Dossier annule", "Date Annulation"),
        ("RFE", "Date RFE"),
    ]

    for status_col, date_col in statuses:
        cstat1, cstat2 = st.columns(2)

        current_status = bool(dossier.get(status_col, False))
        current_date = dossier.get(date_col, pd.NaT)

        new_status = cstat1.checkbox(status_col, value=current_status)
        if new_status:
            new_date = cstat2.date_input(
                date_col,
                value=current_date if pd.notna(current_date) else pd.to_datetime("today"),
            )
        else:
            new_date = ""

        df.loc[index, status_col] = new_status
        df.loc[index, date_col] = pd.to_datetime(new_date) if new_status else ""

    # --- Save ---
    if st.button("💾 Enregistrer les modifications"):
        data["Clients"] = df
        if save_all():
            st.success("Modifications enregistrées !")
        else:
            st.error("Erreur lors de la sauvegarde.")
