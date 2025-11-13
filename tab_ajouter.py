import streamlit as st
import pandas as pd
from common_data import ensure_loaded, save_all, MAIN_FILE


def tab_ajouter():
    st.header("➕ Ajouter un dossier")

    data = ensure_loaded(MAIN_FILE)
    if data is None:
        st.warning("⚠️ Importez d’abord un fichier via l’onglet Fichiers.")
        return

    df = data["Clients"]

    # =========================
    # 🚀 NUMÉRO DOSSIER AUTO
    # =========================
    if df.empty:
        next_id = 1
    else:
        next_id = int(df["Dossier N"].max()) + 1

    st.subheader(f"Numéro de dossier attribué : **{next_id}**")

    # =========================
    # 🔽 Sélections dynamiques
    # =========================
    categories = sorted(df["Categories"].dropna().astype(str).unique().tolist())
    souscats = sorted(df["Sous-categorie"].dropna().astype(str).unique().tolist())
    visas = sorted(df["Visa"].dropna().astype(str).unique().tolist())

    col1, col2, col3 = st.columns(3)
    with col1:
        nom = st.text_input("Nom du client")
    with col2:
        categorie = st.selectbox("Catégorie", [""] + categories)
    with col3:
        souscat = st.selectbox("Sous-catégorie", [""] + souscats)

    visa = st.selectbox("Visa", [""] + visas)

    # =========================
    # 💰 Montants + Acompte 1
    # =========================
    colA, colB = st.columns(2)
    with colA:
        montant_hono = st.number_input("Montant honoraires (US $)", min_value=0.0, step=10.0)
    with colB:
        montant_frais = st.number_input("Autres frais (US $)", min_value=0.0, step=10.0)

    st.markdown("### 💵 Acompte")

    colA1, colA2, colA3 = st.columns(3)
    with colA1:
        acompte1 = st.number_input("Acompte 1 (US$)", min_value=0.0, step=10.0)
    with colA2:
        date_acompte1 = st.date_input("Date Acompte 1")
    with colA3:
        mode_paiement = st.text_input("Mode de paiement")

    # =========================
    # 🛡️ ESCROW
    # =========================
    escrow_check = st.checkbox("Escrow ?")

    # =========================
    # 📌 Enregistrement
    # =========================
    if st.button("💾 Enregistrer le dossier"):
        new_row = {
            "Dossier N": next_id,
            "Nom": nom,
            "Date": pd.Timestamp.today().date(),
            "Categories": categorie,
            "Sous-categorie": souscat,
            "Visa": visa,
            "Montant honoraires (US $)": montant_hono,
            "Autres frais (US $)": montant_frais,
            "Acompte 1": acompte1,
            "Date Acompte 1": pd.to_datetime(date_acompte1),
            "Acompte 2": 0,
            "Date Acompte 2": pd.NaT,
            "Acompte 3": 0,
            "Date Acompte 3": pd.NaT,
            "Acompte 4": 0,
            "Date Acompte 4": pd.NaT,
            "Escrow": "Oui" if escrow_check else "Non",
            "Dossier envoye": pd.NaT,
            "Dossier accepte": pd.NaT,
            "Dossier refuse": pd.NaT,
            "Dossier annule": pd.NaT,
            "RFE": "",
            "Date RFE": pd.NaT,
        }

        data["Clients"] = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

        if save_all():
            st.success("✅ Dossier ajouté et sauvegardé !")
        else:
            st.error("❌ Erreur lors de la sauvegarde.")