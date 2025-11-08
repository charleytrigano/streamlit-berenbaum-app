import streamlit as st
import pandas as pd
import numpy as np
from datetime import date

def tab_ajouter():
    st.header("🧾 Ajouter un dossier client")

    if "data_xlsx" not in st.session_state or not st.session_state["data_xlsx"]:
        st.warning("⚠️ Aucun fichier Excel chargé. Passe d'abord par l'onglet 📄 Fichiers.")
        return

    data = st.session_state["data_xlsx"]

    if "Clients" not in data or "Visa" not in data:
        st.error("❌ Feuille 'Clients' ou 'Visa' manquante dans le fichier Excel.")
        return

    df_clients = data["Clients"].copy()
    df_visa = data["Visa"].copy()

    # 🔍 Normaliser les noms de colonnes
    df_visa.columns = [c.strip().replace("é", "e").replace("è", "e").replace("É", "E").replace("ê", "e") for c in df_visa.columns]

    col_categorie = next((c for c in df_visa.columns if "categorie" in c.lower()), None)
    col_souscat = next((c for c in df_visa.columns if "sous" in c.lower()), None)

    if not col_categorie or not col_souscat:
        st.error("❌ Impossible d’identifier les colonnes 'Catégories' et 'Sous-catégories' dans la feuille Visa.")
        return

    categories = sorted(df_visa[col_categorie].dropna().unique().tolist())

    # ========== Bloc principal ==========
    st.subheader("📋 Informations principales")
    c1, c2, c3 = st.columns([1, 2, 1])
    with c1:
        try:
            last_num = (
                df_clients["Dossier N"].dropna().astype(str).str.extract(r"(\d+)").dropna().astype(int).max().values[0]
            )
            dossier_n = str(last_num + 1)
        except Exception:
            dossier_n = "1"
        st.text_input("Dossier N°", value=dossier_n, disabled=True)
    with c2:
        nom = st.text_input("Nom du client *")
    with c3:
        date_creation = st.date_input("Date (création du dossier)", value=date.today())

    # ========== Catégorie / Sous-catégorie ==========
    st.markdown("### 🗂️ Classification du dossier")
    c4, c5, c6 = st.columns(3)
    with c4:
        categorie = st.selectbox("Catégorie", options=[""] + categories)
    with c5:
        if categorie:
            sous_df = df_visa[df_visa[col_categorie] == categorie]
            sous_categories = sorted(sous_df[col_souscat].dropna().unique().tolist())
        else:
            sous_df = pd.DataFrame()
            sous_categories = []
        sous_categorie = st.selectbox("Sous-catégorie", options=[""] + sous_categories)
    with c6:
        # ⚙️ Détection des visas possibles pour la sous-catégorie
        if categorie and sous_categorie:
            line = df_visa[(df_visa[col_categorie] == categorie) & (df_visa[col_souscat] == sous_categorie)]
            if not line.empty:
                visa_possibles = [
                    col for col in df_visa.columns
                    if col not in [col_categorie, col_souscat]
                    and str(line.iloc[0][col]).strip() == "1"
                ]
            else:
                visa_possibles = []
        else:
            visa_possibles = []
        visa = st.selectbox("Visa", options=[""] + visa_possibles)

    # ========== Détails financiers ==========
    st.markdown("### 💰 Détails financiers")
    c7, c8, c9 = st.columns(3)
    with c7:
        montant_h = st.number_input("Montant honoraires (US $)", min_value=0.0, step=100.0)
    with c8:
        date_acompte1 = st.date_input("Date Acompte 1", value=None)
    with c9:
        acompte1 = st.number_input("Acompte 1", min_value=0.0, step=50.0)

    # ========== Mode de paiement ==========
    st.markdown("### 🏦 Mode de paiement")
    mode_col, cb1, cb2, cb3, cb4 = st.columns([2, 1, 1, 1, 1])
    with mode_col:
        st.write("Sélectionnez un ou plusieurs modes :")
    with cb1:
        cheque = st.checkbox("Chèque")
    with cb2:
        virement = st.checkbox("Virement")
    with cb3:
        carte = st.checkbox("Carte bancaire")
    with cb4:
        venmo = st.checkbox("Venmo")

    mode_paiement = ", ".join(
        [m for m, v in {
            "Chèque": cheque,
            "Virement": virement,
            "Carte bancaire": carte,
            "Venmo": venmo
        }.items() if v]
    )

    # ========== Escrow ==========
    st.markdown("### 🛡️ Escrow")
    escrow_checked = st.checkbox("Activer Escrow pour ce dossier")
    escrow_value = "Oui" if escrow_checked else "Non"

    # ========== Commentaires ==========
    st.markdown("### 🗒️ Commentaires")
    commentaires = st.text_area("Commentaires", height=100)

    # ========== Sauvegarde ==========
    if st.button("💾 Enregistrer le dossier"):
        if not nom.strip():
            st.error("❌ Le nom du client est obligatoire.")
            return

        montant_facture = montant_h
        total_paye = acompte1
        solde = montant_facture - total_paye

        new_row = pd.DataFrame([{
            "Dossier N": dossier_n,
            "Nom": nom.strip(),
            "Date": date_creation.isoformat(),
            "Categories": categorie,
            "Sous-categories": sous_categorie,
            "Visa": visa,
            "Montant honoraires (US $)": montant_h,
            "Acompte 1": acompte1,
            "Date Acompte 1": date_acompte1.isoformat() if date_acompte1 else "",
            "Mode de paiement": mode_paiement,
            "Escrow": escrow_value,
            "Commentaires": commentaires.strip(),
            "Autres frais (US $)": 0.0,
            "Montant facturé": montant_facture,
            "Total payé": total_paye,
            "Solde restant": solde
        }])

        df_clients = pd.concat([df_clients, new_row], ignore_index=True)
        st.session_state["data_xlsx"]["Clients"] = df_clients

        try:
            with pd.ExcelWriter("Clients BL.xlsx", mode="w", engine="openpyxl") as writer:
                for sheet, d in st.session_state["data_xlsx"].items():
                    d.to_excel(writer, sheet_name=sheet, index=False)
            st.success(f"✅ Dossier #{dossier_n} enregistré et sauvegardé avec succès.")
        except Exception:
            st.warning("⚠️ Dossier ajouté en mémoire (sauvegarde locale impossible sur Streamlit Cloud).")

        st.dataframe(new_row, use_container_width=True, height=160)
