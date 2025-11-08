import streamlit as st
import pandas as pd
from datetime import date

def _casefold(s: str) -> str:
    return (s or "").strip().casefold()

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

    # --- Normalisation colonnes Visa ---
    df_visa.columns = [str(c).strip() for c in df_visa.columns]
    col_cat = next((c for c in df_visa.columns if "categorie" in c.lower()), None)
    col_sous = next((c for c in df_visa.columns if "sous" in c.lower()), None)

    if not col_cat or not col_sous:
        st.error("❌ Impossible d'identifier les colonnes Catégories / Sous-catégories dans la feuille Visa.")
        return

    df_visa[col_cat] = df_visa[col_cat].astype(str).str.strip()
    df_visa[col_sous] = df_visa[col_sous].astype(str).str.strip()

    cat_list = sorted([c for c in df_visa[col_cat].dropna().unique().tolist() if c])

    # ==================== Ligne 1 ====================
    c1, c2, c3 = st.columns([1, 2, 1])
    with c1:
        try:
            last_num = (
                df_clients["Dossier N"]
                .dropna().astype(str).str.extract(r"(\d+)").dropna()
                .astype(int).max().values[0]
            )
            dossier_n = str(last_num + 1)
        except Exception:
            dossier_n = "1"
        st.text_input("Dossier N°", dossier_n, disabled=True)
    with c2:
        nom = st.text_input("Nom du client *")
    with c3:
        date_creation = st.date_input("Date (création du dossier)", value=date.today())

    # ==================== Ligne 2 ====================
    c4, c5, c6 = st.columns(3)
    with c4:
        categorie = st.selectbox("Catégorie", options=[""] + cat_list)

    with c5:
        if categorie:
            sous_df = df_visa[df_visa[col_cat].str.casefold().eq(_casefold(categorie))]
            sous_list = sorted([s for s in sous_df[col_sous].dropna().unique().tolist() if s])
        else:
            sous_df = pd.DataFrame(columns=df_visa.columns)
            sous_list = []
        sous_categorie = st.selectbox("Sous-catégorie", options=[""] + sous_list)

    with c6:
        if categorie and sous_categorie and not sous_df.empty:
            line = sous_df[sous_df[col_sous].str.casefold().eq(_casefold(sous_categorie))]
            visa_cols = []
            if not line.empty:
                row = line.iloc[0]
                for col in df_visa.columns:
                    if col in (col_cat, col_sous):
                        continue
                    val = row[col]
                    num = pd.to_numeric(val, errors="coerce")
                    if (pd.notna(num) and int(num) == 1) or str(val).strip().lower() in {"1", "x", "oui", "true"}:
                        visa_cols.append(str(col))
        else:
            visa_cols = []
        visa = st.selectbox("Visa", options=[""] + sorted(visa_cols))

    # ==================== Ligne 3 ====================
    c7, c8, c9 = st.columns(3)
    with c7:
        montant_h = st.number_input("Montant honoraires (US $)", min_value=0.0, step=100.0)
    with c8:
        date_acompte1 = st.date_input("Date Acompte 1", value=None)
    with c9:
        acompte1 = st.number_input("Acompte 1", min_value=0.0, step=50.0)

    # ==================== Ligne 4 ====================
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
    mode_paiement = ", ".join([m for m, v in {
        "Chèque": cheque, "Virement": virement, "Carte bancaire": carte, "Venmo": venmo
    }.items() if v])

    # ==================== Ligne 5 ====================
    st.markdown("### 🛡️ Escrow")
    escrow = st.checkbox("Escrow (activer pour ce dossier)")
    escrow_value = "Oui" if escrow else "Non"

    # ==================== Ligne 6 ====================
    st.markdown("### 🗒️ Commentaires")
    commentaires = st.text_area("Commentaires", height=100)

    # ==================== Enregistrement ====================
    if st.button("💾 Enregistrer le dossier"):
        if not nom.strip():
            st.error("❌ Le nom du client est obligatoire.")
            return

        montant_facture = float(montant_h)
        total_paye = float(acompte1)
        solde = montant_facture - total_paye

        new_row = pd.DataFrame([{
            "Dossier N": dossier_n,
            "Nom": nom.strip(),
            "Date": date_creation.isoformat(),
            "Categories": categorie,
            "Sous-categories": sous_categorie,
            "Visa": visa,
            "Montant honoraires (US $)": montant_facture,
            "Acompte 1": total_paye,
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

        # --- Escrow automatique ---
        if (montant_h == 0 and acompte1 > 0) or escrow:
            escrow_df = st.session_state["data_xlsx"].get("Escrow", pd.DataFrame(columns=[
                "Dossier N", "Nom", "Montant", "Date envoi", "État", "Date réclamation"
            ])).copy()

            new_escrow = pd.DataFrame([{
                "Dossier N": dossier_n,
                "Nom": nom.strip(),
                "Montant": acompte1,
                "Date envoi": date_acompte1.isoformat() if date_acompte1 else date_creation.isoformat(),
                "État": "En attente",
                "Date réclamation": ""
            }])

            escrow_df = pd.concat([escrow_df, new_escrow], ignore_index=True)
            st.session_state["data_xlsx"]["Escrow"] = escrow_df

            st.success(f"💰 Dossier #{dossier_n} ajouté à Escrow (montant {acompte1:.2f} US $).")

        # --- Sauvegarde locale ---
        try:
            with pd.ExcelWriter("Clients BL.xlsx", engine="openpyxl", mode="w") as writer:
                for sheet, df_sheet in st.session_state["data_xlsx"].items():
                    df_sheet.to_excel(writer, index=False, sheet_name=sheet)
            st.success(f"✅ Dossier #{dossier_n} enregistré et sauvegardé avec succès.")
        except Exception:
            st.warning("⚠️ Dossier ajouté en mémoire (sauvegarde locale impossible sur Streamlit Cloud).")

        st.dataframe(new_row, use_container_width=True, height=180)
