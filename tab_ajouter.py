import streamlit as st
import pandas as pd
import numpy as np
from datetime import date, datetime
from pathlib import Path

# ===================== Helpers (détection des colonnes) =====================

def _find_col(df, candidates, default=None):
    """
    Retourne le premier nom de colonne existant dans df parmi candidates.
    Si rien n'est trouvé, retourne default.
    """
    cols_lower = {str(c).strip().lower(): c for c in df.columns}
    for cand in candidates:
        key = str(cand).strip().lower()
        if key in cols_lower:
            return cols_lower[key]
    return default

def _ensure_column(df, col_name, default=np.nan):
    """Crée la colonne si elle n'existe pas."""
    if col_name not in df.columns:
        df[col_name] = default
    return df

def _parse_float(val):
    if val in (None, "", "nan"):
        return 0.0
    try:
        # Remplace virgules par points si l'utilisateur tape au format FR
        return float(str(val).replace(" ", "").replace("\xa0", "").replace(",", "."))
    except:
        return 0.0

def _save_excel_safely(df_dict, excel_path="Clients BL.xlsx"):
    """
    Sauvegarde l'ensemble des feuilles si possible.
    - df_dict: dict {'Feuille': DataFrame}
    - excel_path: fichier cible
    Tente d'écrire localement ; en environnement read-only (Streamlit Cloud),
      la mise à jour en mémoire (session_state) suffit pour le fonctionnement.
    """
    try:
        with pd.ExcelWriter(excel_path, engine="openpyxl", mode="w") as writer:
            for sheet, _df in df_dict.items():
                _df.to_excel(writer, sheet_name=sheet, index=False)
        return True, f"Fichier sauvegardé: {excel_path}"
    except Exception as e:
        return False, f"Sauvegarde locale non effectuée (environnement read-only). Données mises à jour en mémoire. Détail: {e}"

# ===================== Onglet Ajouter =====================

def tab_ajouter():
    st.header("➕ Ajouter un dossier")

    # Vérif de la charge Excel en session
    if "data_xlsx" not in st.session_state or not st.session_state["data_xlsx"]:
        st.warning("⚠️ Aucune donnée disponible. Chargez d'abord le fichier Excel via l'onglet '📄 Fichiers'.")
        return

    data = st.session_state["data_xlsx"]

    # On travaille sur la feuille Clients
    if "Clients" not in data:
        st.error("❌ La feuille 'Clients' est absente du fichier Excel.")
        return

    df_clients = data["Clients"].copy()

    # Détection des colonnes existantes (variantes possibles)
    col_nom  = _find_col(df_clients, ["Nom", "Client", "Name"], default="Nom")
    col_visa = _find_col(df_clients, ["Visa", "Type visa", "Visa Type"], default="Visa")
    col_cat  = _find_col(df_clients, ["Categories", "Catégorie", "Categorie", "category", "Type dossier"], default="Categories")
    col_scat = _find_col(df_clients, ["Sous-categories", "Sous-catégorie", "Sous categorie", "Sous-categorie", "Sous type"], default="Sous-categories")
    col_date = _find_col(df_clients, ["Date", "Date création", "Date d'envoi", "Created at", "Créé le"], default="Date")

    # Colonnes financières
    COL_MONTANT = "Montant honoraires (US $)"
    COL_AUTRES  = "Autres frais (US $)"
    COL_FACTURE = "Montant facturé"
    COL_TP      = "Total payé"
    COL_SOLDE   = "Solde restant"
    COL_A1      = "Acompte 1"
    COL_A1_DATE = "Date Acompte 1"
    COL_MODE    = "Mode de paiement"

    # On s'assure que les principales colonnes existent dans le DataFrame
    for cn in [col_nom, col_visa, col_cat, col_scat, col_date, COL_MONTANT, COL_AUTRES, COL_FACTURE, COL_TP, COL_SOLDE, COL_A1, COL_A1_DATE, COL_MODE]:
        df_clients = _ensure_column(df_clients, cn, default=np.nan)

    # Propositions de choix (liste existante + champ "Autre")
    existing_categories = sorted([c for c in df_clients[col_cat].dropna().astype(str).str.strip().unique() if c])
    existing_souscat    = sorted([c for c in df_clients[col_scat].dropna().astype(str).str.strip().unique() if c])
    existing_visa       = sorted([c for c in df_clients[col_visa].dropna().astype(str).str.strip().unique() if c])

    st.subheader("📝 Informations principales")
    c1, c2 = st.columns(2)
    with c1:
        nom = st.text_input("Nom du client *", value="")
    with c2:
        visa = st.selectbox("Visa", options=(["(Saisir)"] + existing_visa + ["(Autre)"]))
        if visa in ("(Saisir)", "(Autre)"):
            visa = st.text_input("Autre visa (précisez)", value="")

    c3, c4 = st.columns(2)
    with c3:
        cat_choice = st.selectbox("Categories", options=(["(Saisir)"] + existing_categories + ["(Autre)"]))
        if cat_choice in ("(Saisir)", "(Autre)"):
            cat_choice = st.text_input("Autre catégorie (précisez)", value="")
    with c4:
        scat_choice = st.selectbox("Sous-categories", options=(["(Saisir)"] + existing_souscat + ["(Autre)"]))
        if scat_choice in ("(Saisir)", "(Autre)"):
            scat_choice = st.text_input("Autre sous-catégorie (précisez)", value="")

    # Dates : Date de création & Date acompte 1
    st.subheader("📅 Dates")
    c5, c6 = st.columns(2)
    with c5:
        date_creation = st.date_input("Date (création du dossier)", value=date.today())
    with c6:
        date_acompte1 = st.date_input("Date Acompte 1", value=None)

    # Montants
    st.subheader("💵 Montants")
    c7, c8, c9 = st.columns(3)
    with c7:
        montant_h = st.text_input(f"{COL_MONTANT}", value="0")
    with c8:
        autres_f = st.text_input(f"{COL_AUTRES}", value="0")
    with c9:
        acompte1 = st.text_input(f"{COL_A1}", value="0")

    # Mode de paiement (cases à cocher)
    st.subheader("🏦 Mode de paiement (cases à cocher)")
    cb1, cb2, cb3, cb4 = st.columns(4)
    with cb1:
        mp_cheque  = st.checkbox("Chèque", value=False)
    with cb2:
        mp_virmt   = st.checkbox("Virement", value=False)
    with cb3:
        mp_cb      = st.checkbox("Carte de crédit", value=False)
    with cb4:
        mp_venmo   = st.checkbox("Venmo", value=False)

    selected_modes = []
    if mp_cheque: selected_modes.append("Chèque")
    if mp_virmt:  selected_modes.append("Virement")
    if mp_cb:     selected_modes.append("Carte de crédit")
    if mp_venmo:  selected_modes.append("Venmo")
    mode_str = ", ".join(selected_modes)

    st.markdown("---")

    # Bouton d'enregistrement
    if st.button("💾 Enregistrer le dossier"):
        # Validation minimale
        if not nom.strip():
            st.error("Le nom du client est obligatoire.")
            return

        # Parsing numerique
        montant_h_v = _parse_float(montant_h)
        autres_f_v  = _parse_float(autres_f)
        acompte1_v  = _parse_float(acompte1)

        # Calculs
        montant_facture = montant_h_v + autres_f_v
        total_paye      = acompte1_v  # on retire Acompte 2-4
        solde_restant   = montant_facture - total_paye

        # Construction de la nouvelle ligne alignée sur les colonnes en place
        new_row = {c: np.nan for c in df_clients.columns}

        new_row[col_nom]  = nom.strip()
        new_row[col_visa] = visa.strip()
        new_row[col_cat]  = cat_choice.strip()
        new_row[col_scat] = scat_choice.strip()

        # Dates au format ISO (YYYY-MM-DD) pour consistence
        try:
            new_row[col_date] = pd.to_datetime(date_creation).date().isoformat()
        except:
            new_row[col_date] = ""

        try:
            new_row[COL_A1_DATE] = pd.to_datetime(date_acompte1).date().isoformat() if date_acompte1 else ""
        except:
            new_row[COL_A1_DATE] = ""

        new_row[COL_MONTANT] = montant_h_v
        new_row[COL_AUTRES]  = autres_f_v
        new_row[COL_A1]      = acompte1_v
        new_row[COL_FACTURE] = montant_facture
        new_row[COL_TP]      = total_paye
        new_row[COL_SOLDE]   = solde_restant
        new_row[COL_MODE]    = mode_str

        # Append
        df_clients = pd.concat([df_clients, pd.DataFrame([new_row])], ignore_index=True)

        # Mise à jour en mémoire
        st.session_state["data_xlsx"]["Clients"] = df_clients

        # Tentative de sauvegarde sur disque (si permis)
        ok, msg = _save_excel_safely(st.session_state["data_xlsx"], excel_path="Clients BL.xlsx")

        st.success("✅ Dossier ajouté avec succès.")
        if ok:
            st.info(msg)
        else:
            st.warning(msg)

        # Affichage de la ligne ajoutée
        st.markdown("**Aperçu de la ligne ajoutée :**")
        ap_cols = [col_nom, col_visa, col_cat, col_scat, col_date, COL_MONTANT, COL_AUTRES, COL_A1, COL_A1_DATE, COL_FACTURE, COL_TP, COL_SOLDE, COL_MODE]
        ap_cols = [c for c in ap_cols if c in df_clients.columns]
        st.dataframe(pd.DataFrame([new_row])[ap_cols], use_container_width=True, height=120)
