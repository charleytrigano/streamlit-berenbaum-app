import streamlit as st
import pandas as pd
from datetime import date

from common_data import ensure_loaded, save_all, MAIN_FILE


def _safe_unique(df: pd.DataFrame, col: str):
    """Retourne la liste triée des valeurs uniques non nulles d'une colonne, ou [] si absente/vide."""
    if col not in df.columns:
        return []
    s = df[col].dropna().astype(str)
    vals = sorted([v for v in s.unique().tolist() if v.strip() != ""])
    return vals


def tab_ajouter():
    st.header("➕ Ajouter un dossier")

    # Charger les données globales
    data = ensure_loaded(MAIN_FILE)

    if "Clients" not in data:
        st.error("❌ La feuille 'Clients' est absente du fichier Excel.")
        return

    df = data["Clients"].copy()

    if df.empty:
        # On crée un DF vide avec les colonnes attendues si besoin
        cols = [
            "Dossier N",
            "Nom",
            "Date",
            "Catégories",
            "Sous-catégorie",
            "Visa",
            "Montant honoraires (US $)",
            "Autres frais (US $)",
            "Acompte 1",
            "Date Acompte 1",
            "Mode paiement 1",
            "Acompte 2",
            "Date Acompte 2",
            "Mode paiement 2",
            "Acompte 3",
            "Date Acompte 3",
            "Mode paiement 3",
            "Acompte 4",
            "Date Acompte 4",
            "Mode paiement 4",
            "Escrow",
            "Dossier envoyé",
            "Date envoi dossier",
            "Dossier accepté",
            "Date accepté",
            "Dossier refusé",
            "Date refus",
            "Dossier annulé",
            "Date annulation",
            "RFE",
            "Date RFE",
            "Commentaires",
        ]
        df = pd.DataFrame(columns=cols)

    # Déterminer le prochain numéro de dossier
    if "Dossier N" in df.columns and not df["Dossier N"].dropna().empty:
        try:
            next_num = int(pd.to_numeric(df["Dossier N"], errors="coerce").max()) + 1
        except Exception:
            next_num = 1
    else:
        next_num = 1

    # Listes déroulantes basées sur les données existantes
    cats = _safe_unique(df, "Catégories")
    sous_cats_all = _safe_unique(df, "Sous-catégorie")
    visas = _safe_unique(df, "Visa")

    # Formulaire
    with st.form("form_ajouter_dossier"):
        st.markdown(f"**Dossier N° : `{next_num}`**")

        # Ligne 1 : Nom + Date (création)
        c1, c2 = st.columns(2)
        with c1:
            nom = st.text_input("Nom du client")
        with c2:
            date_creation = st.date_input("Date (création)", value=date.today())

        # Ligne 2 : Catégorie / Sous-catégorie / Visa
        c3, c4, c5 = st.columns(3)

        with c3:
            cat = st.selectbox(
                "Catégorie",
                [""] + cats,
                index=0
            )

        # Sous-catégories filtrées par catégorie si possible
        if cat:
            sous_cats_filtered = sorted(
                df.loc[df["Catégories"] == cat, "Sous-catégorie"]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            )
        else:
            sous_cats_filtered = sous_cats_all

        with c4:
            sous_cat = st.selectbox(
                "Sous-catégorie",
                [""] + sous_cats_filtered,
                index=0
            )

        with c5:
            visa = st.selectbox(
                "Visa",
                [""] + visas,
                index=0
            )

        # Ligne 3 : Montants
        c6, c7, c8 = st.columns(3)
        with c6:
            honoraires = st.number_input(
                "Montant honoraires (US $)",
                min_value=0.0,
                step=50.0,
                format="%.2f",
            )
        with c7:
            autres_frais = st.number_input(
                "Autres frais (US $)",
                min_value=0.0,
                step=50.0,
                format="%.2f",
            )
        with c8:
            acompte1 = st.number_input(
                "Acompte 1",
                min_value=0.0,
                step=50.0,
                format="%.2f",
            )

        # Ligne 4 : Date acompte 1 + mode de paiement + Escrow
        c9, c10, c11 = st.columns(3)
        with c9:
            date_acompte1 = st.date_input("Date Acompte 1", value=date.today())
        with c10:
            mode_paiement1 = st.selectbox(
                "Mode de paiement",
                ["", "Chèque", "Virement", "Carte bancaire", "Venmo"],
            )
        with c11:
            escrow = st.checkbox("Escrow")

        # Ligne 5 : Commentaires
        commentaires = st.text_area("Commentaires")

        submitted = st.form_submit_button("✅ Enregistrer le dossier")

    if not submitted:
        return

    # Validation minimum
    if not nom.strip():
        st.error("❌ Le nom du client est obligatoire.")
        return

    # Construction de la nouvelle ligne
    new_row = {col: None for col in df.columns}

    new_row["Dossier N"] = next_num
    new_row["Nom"] = nom.strip()
    new_row["Date"] = pd.to_datetime(date_creation)

    if "Catégories" in df.columns:
        new_row["Catégories"] = cat or None
    if "Sous-catégorie" in df.columns:
        new_row["Sous-catégorie"] = sous_cat or None
    if "Visa" in df.columns:
        new_row["Visa"] = visa or None

    if "Montant honoraires (US $)" in df.columns:
        new_row["Montant honoraires (US $)"] = float(honoraires)
    if "Autres frais (US $)" in df.columns:
        new_row["Autres frais (US $)"] = float(autres_frais)

    if "Acompte 1" in df.columns:
        new_row["Acompte 1"] = float(acompte1)
    if "Date Acompte 1" in df.columns:
        new_row["Date Acompte 1"] = pd.to_datetime(date_acompte1)
    if "Mode paiement 1" in df.columns:
        new_row["Mode paiement 1"] = mode_paiement1 or None

    # On remet Acompte 2/3/4 à zéro si ces colonnes existent
    for n in (2, 3, 4):
        col_a = f"Acompte {n}"
        col_d = f"Date Acompte {n}"
        col_m = f"Mode paiement {n}"
        if col_a in df.columns:
            new_row[col_a] = 0.0
        if col_d in df.columns:
            new_row[col_d] = pd.NaT
        if col_m in df.columns:
            new_row[col_m] = None

    if "Escrow" in df.columns:
        new_row["Escrow"] = bool(escrow)

    # Statuts / dates initialisés à vide si colonnes présentes
    status_cols = [
        "Dossier envoyé",
        "Date envoi dossier",
        "Dossier accepté",
        "Date accepté",
        "Dossier refusé",
        "Date refus",
        "Dossier annulé",
        "Date annulation",
        "RFE",
        "Date RFE",
    ]
    for col in status_cols:
        if col in df.columns and col not in new_row:
            new_row[col] = None

    if "Commentaires" in df.columns:
        new_row["Commentaires"] = commentaires or None

    # Ajouter la ligne au DataFrame
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    data["Clients"] = df
    st.session_state["data_xlsx"] = data

    # Sauvegarde (Drive + local selon ta config dans common_data)
    save_all()

    st.success(f"✅ Dossier {next_num} ajouté avec succès.")
    st.rerun()