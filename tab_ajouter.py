import streamlit as st
import pandas as pd
import numpy as np
from datetime import date

# ===================== Onglet AJOUTER =====================

def tab_ajouter():
    st.header("➕ Ajouter un dossier")

    # Vérifier que le fichier Excel est chargé
    if "data_xlsx" not in st.session_state or not st.session_state["data_xlsx"]:
        st.warning("⚠️ Aucune donnée disponible. Chargez d'abord le fichier Excel via l'onglet 📄 Fichiers.")
        return

    data = st.session_state["data_xlsx"]

    # Vérifier la présence de la feuille Clients
    if "Clients" not in data:
        st.error("❌ Feuille 'Clients' manquante.")
        return

    df = data["Clients"].copy()

    # On s’assure que toutes les colonnes nécessaires existent
    required_cols = [
        "Nom", "Visa", "Categories", "Sous-categories",
        "Date", "Montant honoraires (US $)", "Autres frais (US $)",
        "Acompte 1", "Date Acompte 1", "Mode de paiement",
        "Montant facturé", "Total payé", "Solde restant"
    ]
    for col in required_cols:
        if col not in df.columns:
            df[col] = np.nan

    # ===================== FORMULAIRE =====================

    st.subheader("🧾 Informations principales")

    c1, c2 = st.columns(2)
    with c1:
        nom = st.text_input("Nom du client *")
        categorie = st.text_input("Catégorie")
    with c2:
        visa = st.text_input("Visa")
        sous_categorie = st.text_input("Sous-catégorie")

    st.subheader("📅 Dates")
    c3, c4 = st.columns(2)
    with c3:
        date_creation = st.date_input("Date (création du dossier)", value=date.today())
    with c4:
        date_acompte1 = st.date_input("Date Acompte 1", value=None)

    st.subheader("💵 Montants")
    c5, c6, c7 = st.columns(3)
    with c5:
        montant_h = st.number_input("Montant honoraires (US $)", min_value=0.0, step=100.0)
    with c6:
        autres_f = st.number_input("Autres frais (US $)", min_value=0.0, step=50.0)
    with c7:
        acompte1 = st.number_input("Acompte 1", min_value=0.0, step=50.0)

    st.subheader("🏦 Mode de paiement")
    cb1, cb2, cb3, cb4 = st.columns(4)
    with cb1:
        chq = st.checkbox("Chèque")
    with cb2:
        vir = st.checkbox("Virement")
    with cb3:
        cb = st.checkbox("Carte de crédit")
    with cb4:
        venmo = st.checkbox("Venmo")

    mode_paiement = ", ".join(
        [m for m, v in {
            "Chèque": chq,
            "Virement": vir,
            "Carte de crédit": cb,
            "Venmo": venmo
        }.items() if v]
    )

    st.markdown("---")

    # ===================== SAUVEGARDE =====================

    if st.button("💾 Enregistrer le dossier"):
        if not nom.strip():
            st.error("Le nom du client est obligatoire.")
            return

        montant_facture = montant_h + autres_f
        total_paye = acompte1
        solde = montant_facture - total_paye

        new_row = pd.DataFrame([{
            "Nom": nom,
            "Visa": visa,
            "Categories": categorie,
            "Sous-categories": sous_categorie,
            "Date": date_creation.isoformat(),
            "Montant honoraires (US $)": montant_h,
            "Autres frais (US $)": autres_f,
            "Acompte 1": acompte1,
            "Date Acompte 1": date_acompte1.isoformat() if date_acompte1 else "",
            "Mode de paiement": mode_paiement,
            "Montant facturé": montant_facture,
            "Total payé": total_paye,
            "Solde restant": solde
        }])

        df = pd.concat([df, new_row], ignore_index=True)
        st.session_state["data_xlsx"]["Clients"] = df

        # Sauvegarde locale si possible
        try:
            with pd.ExcelWriter("Clients BL.xlsx", mode="w", engine="openpyxl") as writer:
                for sheet, d in st.session_state["data_xlsx"].items():
                    d.to_excel(writer, sheet_name=sheet, index=False)
            st.success("✅ Dossier ajouté et sauvegardé avec succès.")
        except Exception:
            st.warning("⚠️ Dossier ajouté en mémoire (sauvegarde locale impossible sur Streamlit Cloud).")

        st.dataframe(new_row, use_container_width=True)
