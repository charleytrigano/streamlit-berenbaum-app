import streamlit as st
import pandas as pd
import numpy as np
from datetime import date

def tab_ajouter():
    st.header("🧾 Ajouter un dossier client")

    # Vérifie la présence du fichier
    if "data_xlsx" not in st.session_state or not st.session_state["data_xlsx"]:
        st.warning("⚠️ Aucun fichier Excel chargé. Passe d'abord par l'onglet 📄 Fichiers.")
        return

    data = st.session_state["data_xlsx"]
    if "Clients" not in data:
        st.error("❌ Feuille 'Clients' manquante dans le fichier Excel.")
        return

    df = data["Clients"].copy()

    # Colonnes nécessaires
    required_cols = [
        "Dossier N", "Nom", "Date", "Categories", "Sous-categories", "Visa",
        "Montant honoraires (US $)", "Acompte 1", "Date Acompte 1",
        "Mode de paiement", "Escrow", "Commentaires",
        "Autres frais (US $)", "Montant facturé", "Total payé", "Solde restant"
    ]
    for col in required_cols:
        if col not in df.columns:
            df[col] = np.nan

    # ========== NUMÉRO DE DOSSIER AUTOMATIQUE ==========
    try:
        last_num = df["Dossier N"].dropna().astype(str).str.extract(r'(\d+)').dropna().astype(int).max().values[0]
        dossier_n = str(last_num + 1)
    except Exception:
        dossier_n = "1"

    # ===================== LIGNE 1 =====================
    st.subheader("📋 Informations principales")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        st.text_input("Dossier N°", value=dossier_n, disabled=True)
    with col2:
        nom = st.text_input("Nom du client *")
    with col3:
        date_creation = st.date_input("Date (création du dossier)", value=date.today())

    # ===================== LIGNE 2 =====================
    st.markdown("### 🗂️ Classification du dossier")

    c4, c5, c6 = st.columns(3)
    with c4:
        categorie = st.text_input("Catégorie")
    with c5:
        sous_categorie = st.text_input("Sous-catégorie")
    with c6:
        visa = st.text_input("Visa")

    # ===================== LIGNE 3 =====================
    st.markdown("### 💰 Détails financiers")

    c7, c8, c9 = st.columns(3)
    with c7:
        montant_h = st.number_input("Montant honoraires (US $)", min_value=0.0, step=100.0)
    with c8:
        date_acompte1 = st.date_input("Date Acompte 1", value=None)
    with c9:
        acompte1 = st.number_input("Acompte 1", min_value=0.0, step=50.0)

    # ===================== LIGNE 4 =====================
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

    # ===================== LIGNE 5 =====================
    st.markdown("### 🛡️ Escrow")
    escrow = st.text_input("Référence Escrow (si applicable)")

    # ===================== LIGNE 6 =====================
    st.markdown("### 🗒️ Commentaires")
    commentaires = st.text_area("Commentaires", height=100)

    # ===================== SAUVEGARDE =====================
    st.markdown("---")
    if st.button("💾 Enregistrer le dossier"):
        if not nom.strip():
            st.error("Le nom du client est obligatoire.")
            return

        montant_facture = montant_h
        total_paye = acompte1
        solde = montant_facture - total_paye

        new_row = pd.DataFrame([{
            "Dossier N": dossier_n,
            "Nom": nom.strip(),
            "Date": date_creation.isoformat(),
            "Categories": categorie.strip(),
            "Sous-categories": sous_categorie.strip(),
            "Visa": visa.strip(),
            "Montant honoraires (US $)": montant_h,
            "Acompte 1": acompte1,
            "Date Acompte 1": date_acompte1.isoformat() if date_acompte1 else "",
            "Mode de paiement": mode_paiement,
            "Escrow": escrow.strip(),
            "Commentaires": commentaires.strip(),
            "Autres frais (US $)": 0.0,
            "Montant facturé": montant_facture,
            "Total payé": total_paye,
            "Solde restant": solde
        }])

        df = pd.concat([df, new_row], ignore_index=True)
        st.session_state["data_xlsx"]["Clients"] = df

        try:
            with pd.ExcelWriter("Clients BL.xlsx", mode="w", engine="openpyxl") as writer:
                for sheet, d in st.session_state["data_xlsx"].items():
                    d.to_excel(writer, sheet_name=sheet, index=False)
            st.success("✅ Dossier ajouté et sauvegardé avec succès.")
        except Exception:
            st.warning("⚠️ Dossier ajouté en mémoire (sauvegarde locale impossible sur Streamlit Cloud).")

        st.markdown("### ✅ Aperçu du dossier ajouté")
        st.dataframe(new_row, use_container_width=True, height=160)
