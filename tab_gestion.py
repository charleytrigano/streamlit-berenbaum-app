import streamlit as st
import pandas as pd
from common_data import ensure_loaded, save_all, MAIN_FILE


def tab_gestion():
    st.header("✏️ / 🗑️ Gestion d’un dossier")

    data = ensure_loaded(MAIN_FILE)
    if data is None:
        st.warning("Aucun fichier chargé.")
        return

    df = data["Clients"]

    # -------------------------
    # Sélection du dossier
    # -------------------------

    st.subheader("📁 Sélection du dossier")

    # Liste des dossiers valides
    dossier_list = (
        pd.to_numeric(df["Dossier N"], errors="coerce")
        .dropna()
        .astype(int)
        .tolist()
    )

    if not dossier_list:
        st.warning("Aucun dossier existant dans le fichier.")
        return

    selected = st.selectbox("Choisir un Dossier N", dossier_list)

    dossier = df[df["Dossier N"] == selected].iloc[0]

    # -------------------------
    # SECTION 1 — Informations générales
    # -------------------------

    st.subheader("👤 Informations générales")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        nom = st.text_input("Nom", dossier["Nom"])
    with col2:
        categorie = st.text_input("Catégorie", dossier["Categories"])
    with col3:
        sous_cat = st.text_input("Sous-catégorie", dossier["Sous-categorie"])
    with col4:
        visa = st.text_input("Visa", dossier["Visa"])

    # -------------------------
    # SECTION 2 — Montants
    # -------------------------

    st.subheader("💰 Montants")

    colA, colB = st.columns(2)
    with colA:
        montant = st.number_input(
            "Montant honoraires (US $)",
            min_value=0.0,
            value=float(dossier["Montant honoraires (US $)"] or 0),
            step=50.0,
        )

    with colB:
        autres_frais = st.number_input(
            "Autres frais (US $)",
            min_value=0.0,
            value=float(dossier["Autres frais (US $)"] or 0),
            step=10.0,
        )

    # -------------------------
    # SECTION 3 — Acomptes
    # -------------------------

    st.subheader("💵 Acomptes")

    def acompte_section(num):
        col1, col2, col3 = st.columns(3)

        with col1:
            montant_val = st.number_input(
                f"Acompte {num}",
                min_value=0.0,
                value=float(dossier[f'Acompte {num}'] or 0),
                step=10.0,
            )

        with col2:
            date_raw = dossier.get(f"Date Acompte {num}", "")
            date_val = (
                pd.to_datetime(date_raw).date()
                if pd.notna(date_raw) and str(date_raw).strip() != ""
                else None
            )
            date_val = st.date_input(f"Date acompte {num}", value=date_val)

        with col3:
            mode_val = st.text_input(
                f"Mode paiement {num}", dossier.get(f"Mode Paiement {num}", "")
            )

        return montant_val, date_val, mode_val

    acompte1, date1, mode1 = acompte_section(1)
    acompte2, date2, mode2 = acompte_section(2)
    acompte3, date3, mode3 = acompte_section(3)
    acompte4, date4, mode4 = acompte_section(4)

    # -------------------------
    # SECTION 4 — Statuts
    # -------------------------

    st.subheader("📌 Statuts du dossier")

    def statut_field(label, col_name_date, col_name_flag):
        col1, col2 = st.columns([1, 1])

        with col1:
            flag = st.checkbox(label, value=bool(dossier.get(col_name_flag, "")))

        with col2:
            raw_date = dossier.get(col_name_date, "")
            date_val = (
                pd.to_datetime(raw_date).date()
                if pd.notna(raw_date) and str(raw_date).strip() != ""
                else None
            )

            # Si la case est cochée → date obligatoire
            date_output = st.date_input(
                f"Date {label.lower()}", value=date_val, disabled=not flag
            )

        return flag, date_output

    envoye, date_envoye = statut_field("Dossier envoyé", "Dossier envoye", "Dossier envoye_flag")
    accepte, date_accepte = statut_field("Dossier accepté", "Dossier accepte", "Dossier accepte_flag")
    refuse, date_refuse = statut_field("Dossier refusé", "Dossier refuse", "Dossier refuse_flag")
    annule, date_annule = statut_field("Dossier annulé", "Dossier annule", "Dossier annule_flag")
    rfe, date_rfe = statut_field("RFE", "Date RFE", "RFE_flag")

    # -------------------------
    # ENREGISTREMENT
    # -------------------------

    if st.button("💾 Enregistrer les modifications"):
        idx = df.index[df["Dossier N"] == selected][0]

        df.at[idx, "Nom"] = nom
        df.at[idx, "Categories"] = categorie
        df.at[idx, "Sous-categorie"] = sous_cat
        df.at[idx, "Visa"] = visa

        df.at[idx, "Montant honoraires (US $)"] = montant
        df.at[idx, "Autres frais (US $)"] = autres_frais

        df.at[idx, "Acompte 1"] = acompte1
        df.at[idx, "Date Acompte 1"] = date1
        df.at[idx, "Mode Paiement 1"] = mode1

        df.at[idx, "Acompte 2"] = acompte2
        df.at[idx, "Date Acompte 2"] = date2
        df.at[idx, "Mode Paiement 2"] = mode2

        df.at[idx, "Acompte 3"] = acompte3
        df.at[idx, "Date Acompte 3"] = date3
        df.at[idx, "Mode Paiement 3"] = mode3

        df.at[idx, "Acompte 4"] = acompte4
        df.at[idx, "Date Acompte 4"] = date4
        df.at[idx, "Mode Paiement 4"] = mode4

        df.at[idx, "Dossier envoye"] = date_envoye if envoye else ""
        df.at[idx, "Dossier accepte"] = date_accepte if accepte else ""
        df.at[idx, "Dossier refuse"] = date_refuse if refuse else ""
        df.at[idx, "Dossier annule"] = date_annule if annule else ""
        df.at[idx, "RFE"] = date_rfe if rfe else ""

        save_all()

        st.success("✅ Modifications enregistrées !")
