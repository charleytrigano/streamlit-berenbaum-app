import streamlit as st
import pandas as pd
from common_data import column_map, save_all, MAIN_FILE

def tab_ajouter():
    st.header("➕ Ajouter un dossier")

    data = st.session_state.get("data_xlsx", {})
    df = data.get("Clients", pd.DataFrame(columns=column_map.values()))

    # Détection du prochain numéro de dossier
    if "Dossier N" in df.columns and not df["Dossier N"].dropna().empty:
        next_num = int(df["Dossier N"].max()) + 1
    else:
        next_num = 1

    st.subheader(f"Nouveau Dossier : **{next_num}**")

    with st.form("ajouter_formulaire"):
        col1, col2 = st.columns(2)

        nom = col1.text_input("Nom")
        date = col2.date_input("Date")

        # Catégorie / Sous-catégorie / Visa
        col3, col4, col5 = st.columns(3)

        categories_existantes = sorted(df["Catégories"].dropna().unique().tolist())
        cat = col3.selectbox("Catégorie", [""] + categories_existantes)

        sous_cat_existants = sorted(df["Sous-catégorie"].dropna().unique().tolist())
        sous_cat = col4.selectbox("Sous-catégorie", [""] + sous_cat_existants)

        visa_existants = sorted(df["Visa"].dropna().unique().tolist())
        visa = col5.selectbox("Visa", [""] + visa_existants)

        # Montants
        col6, col7 = st.columns(2)
        montant_h = col6.number_input("Montant honoraires (US $)", min_value=0.0, step=10.0)
        autres_frais = col7.number_input("Autres frais (US $)", min_value=0.0, step=1.0)

        # Acompte
        col8, col9, col10 = st.columns(3)
        acompte1 = col8.number_input("Acompte 1", min_value=0.0, step=10.0)
        date_acompte1 = col9.date_input("Date Acompte 1")
        mode_acompte1 = col10.text_input("Mode Paiement 1")

        escrow = st.checkbox("Escrow ?")

        submitted = st.form_submit_button("Enregistrer")

    if submitted:
        new_row = {
            "Dossier N": next_num,
            "Nom": nom,
            "Date": pd.to_datetime(date),
            "Catégories": cat,
            "Sous-catégorie": sous_cat,
            "Visa": visa,
            "Montant honoraires (US $)": montant_h,
            "Autres frais (US $)": autres_frais,
            "Acompte 1": acompte1,
            "Date Acompte 1": pd.to_datetime(date_acompte1),
            "Mode Paiement 1": mode_acompte1,
            "Acompte 2": 0,
            "Date Acompte 2": pd.NaT,
            "Mode Paiement 2": "",
            "Acompte 3": 0,
            "Date Acompte 3": pd.NaT,
            "Mode Paiement 3": "",
            "Acompte 4": 0,
            "Date Acompte 4": pd.NaT,
            "Mode Paiement 4": "",
            "Dossier Envoye": "",
            "Date Envoye": pd.NaT,
            "Escrow": "Oui" if escrow else "Non",
        }

        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        st.session_state["data_xlsx"]["Clients"] = df

        if save_all(st.session_state["data_xlsx"], MAIN_FILE):
            st.success("Dossier ajouté et sauvegardé sur Drive ✔")
        else:
            st.error("Erreur lors de la sauvegarde.")

