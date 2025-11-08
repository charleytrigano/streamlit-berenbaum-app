import streamlit as st
import pandas as pd
from datetime import date

def tab_ajouter():
    st.header("🧾 Ajouter un dossier client")

    # Vérifie si les données sont chargées
    if "data_xlsx" not in st.session_state or not st.session_state["data_xlsx"]:
        st.warning("⚠️ Aucun fichier Excel chargé. Passe d'abord par l'onglet 📄 Fichiers.")
        return

    data = st.session_state["data_xlsx"]
    if "Clients" not in data or "Visa" not in data:
        st.error("❌ Feuille 'Clients' ou 'Visa' manquante dans le fichier Excel.")
        return

    df_clients = data["Clients"].copy()
    df_visa = data["Visa"].copy()

    # Normalisation colonnes Visa
    df_visa.columns = [c.strip().replace("é", "e").replace("è", "e").replace("ê", "e") for c in df_visa.columns]
    col_cat = next((c for c in df_visa.columns if "categorie" in c.lower()), None)
    col_sous = next((c for c in df_visa.columns if "sous" in c.lower()), None)

    if not col_cat or not col_sous:
        st.error("❌ Impossible d'identifier les colonnes Catégories / Sous-catégories dans la feuille Visa.")
        return

    # ========= Ligne 1 : Numéro, Nom, Date =========
    c1, c2, c3 = st.columns([1, 2, 1])
    with c1:
        try:
            last_num = (
                df_clients["Dossier N"].dropna().astype(str).str.extract(r"(\d+)").dropna().astype(int).max().values[0]
            )
            dossier_n = str(last_num + 1)
        except Exception:
            dossier_n = "1"
        st.text_input("Dossier N°", dossier_n, disabled=True)
    with c2:
        nom = st.text_input("Nom du client *")
    with c3:
        date_creation = st.date_input("Date (création du dossier)", value=date.today())

    # ========= Ligne 2 : Catégorie, Sous-catégorie, Visa =========
    c4, c5, c6 = st.columns(3)
    with c4:
        cat_list = sorted(df_visa[col_cat].dropna().unique().tolist())
        categorie = st.selectbox("Catégorie", options=[""] + cat_list)
    with c5:
        if categorie:
            sous_df = df_visa[df_visa[col_cat] == categorie]
            sous_list = sorted(sous_df[col_sous].dropna().unique().tolist())
        else:
            sous_df = pd.DataFrame()
            sous_list = []
        sous_categorie = st.selectbox("Sous-catégorie", options=[""] + sous_list)
    with c6:
        if categorie and sous_categorie and not sous_df.empty:
            line = sous_df[sous_df[col_sous] == sous_categorie]
            if not line.empty:
                visa_cols = [
                    col for col in df_visa.columns
                    if col not in [col_cat, col_sous]
                    and str(line.iloc[0][col]).strip() == "1"
                ]
            else:
                visa_cols = []
        else:
            visa_cols = []
        visa = st.selectbox("Visa", options=[""] + visa_cols)

    # ========= Ligne 3 : Finances =========
    c7, c8, c9 = st.columns(3)
    with c7:
        montant_h = st.number_input("Montant honoraires (US $)", min_value=0.0, step=100.0)
    with c8:
        date_acompte1 = st.date_input("Date Acompte 1", value=None)
    with c9:
        acompte1 = st.number_input("Acompte 1", min_value=0.0, step=50.0)

    # ========= Ligne 4 : Mode de paiement =========
    st.markdown("### 🏦 Mode de paiement")
    colm, cb1, cb2, cb3, cb4 = st.columns([2, 1, 1, 1, 1])
    with colm:
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

    # ========= Ligne 5 : Escrow =========
    st.markdown("### 🛡️ Escrow")
    escrow = st.checkbox("Escrow (activer pour ce dossier)")
    escrow_value = "Oui" if escrow else "Non"

    # ========= Ligne 6 : Commentaires =========
    st.markdown("### 🗒️ Commentaires")
    commentaires = st.text_area("Commentaires", height=100)

    # ========= Enregistrement =========
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
            with pd.ExcelWriter("Clients BL.xlsx", engine="openpyxl", mode="w") as writer:
                for sheet, df_sheet in st.session_state["data_xlsx"].items():
                    df_sheet.to_excel(writer, index=False, sheet_name=sheet)
            st.success(f"✅ Dossier #{dossier_n} enregistré et sauvegardé avec succès.")
        except Exception:
            st.warning("⚠️ Dossier ajouté en mémoire (sauvegarde locale impossible sur Streamlit Cloud).")

        st.dataframe(new_row, use_container_width=True, height=180)
