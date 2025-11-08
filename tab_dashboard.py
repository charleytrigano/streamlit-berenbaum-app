import streamlit as st
import pandas as pd
from datetime import datetime

# ---------- Helpers ----------
def _norm_cols(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    mapping_candidates = {
        "Visa": ["visa", "type visa", "type_de_visa", "type-visa"],
        "Catégorie": ["catégorie", "categorie", "catégorie ", "category"],
        "Sous-catégorie": ["sous-catégorie", "sous categorie", "sous-categorie", "subcategory"],
        "Année": ["année", "annee", "year"],
        "Mois": ["mois", "month"],
        "Montant honoraires (US $)": ["montant honoraires (us $)", "honoraires", "montant honoraires"],
        "Autres frais (US $)": ["autres frais (us $)", "autres frais"],
        "Acompte 1": ["acompte 1", "a1", "acompte1"],
        "Acompte 2": ["acompte 2", "a2", "acompte2"],
        "Acompte 3": ["acompte 3", "a3", "acompte3"],
        "Acompte 4": ["acompte 4", "a4", "acompte4"],
        "Nom": ["nom", "client", "full name", "name"],
        "_date_probe_": ["date", "date création", "date d'envoi", "créé le", "created at", "created_on"],
    }

    lower2orig = {c.strip().lower(): c for c in df.columns}

    def find_col(cands):
        for cand in cands:
            if cand in lower2orig:
                return lower2orig[cand]
        return None

    # Renommer les colonnes connues
    for target, cands in mapping_candidates.items():
        if target == "_date_probe_":
            continue
        if target not in df.columns:
            found = find_col([c.strip().lower() for c in cands])
            if found:
                df.rename(columns={found: target}, inplace=True)

    # Colonnes numériques manquantes
    for col in ["Montant honoraires (US $)", "Autres frais (US $)", "Acompte 1", "Acompte 2", "Acompte 3", "Acompte 4"]:
        if col not in df.columns:
            df[col] = 0
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # Calculs principaux
    df["Montant facturé"] = df["Montant honoraires (US $)"] + df["Autres frais (US $)"]
    df["Total payé"] = df[["Acompte 1", "Acompte 2", "Acompte 3", "Acompte 4"]].sum(axis=1)
    df["Solde restant"] = df["Montant facturé"] - df["Total payé"]

    # Gestion des dates pour Année / Mois
    mois_fr = ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
               "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"]

    if ("Année" not in df.columns) or ("Mois" not in df.columns):
        date_col = None
        for probe in mapping_candidates["_date_probe_"]:
            if probe in lower2orig:
                date_col = lower2orig[probe]
                break

        if date_col is not None:
            parsed = pd.to_datetime(df[date_col], errors="coerce", dayfirst=True, infer_datetime_format=True)
            if "Année" not in df.columns:
                df["Année"] = parsed.dt.year.fillna(0).astype(int).replace(0, "")
            if "Mois" not in df.columns:
                df["Mois"] = parsed.dt.month.map(lambda x: mois_fr[int(x)-1] if 1 <= int(x) <= 12 else "")
        else:
            if "Année" not in df.columns:
                df["Année"] = ""
            if "Mois" not in df.columns:
                df["Mois"] = ""

    for c in ["Catégorie", "Sous-catégorie", "Visa"]:
        if c not in df.columns:
            df[c] = ""

    return df


# ---------- Tableau de bord principal ----------
def tab_dashboard():
    """Tableau de bord principal - synthèse financière avec filtres robustes."""
    st.header("📊 Tableau de bord")

    if "data_xlsx" not in st.session_state or not st.session_state["data_xlsx"]:
        st.warning("⚠️ Aucune donnée disponible. Chargez d'abord le fichier Excel via l'onglet '📄 Fichiers'.")
        return

    data = st.session_state["data_xlsx"]
    if "Clients" not in data:
        st.error("❌ La feuille 'Clients' est absente du fichier Excel.")
        return

    df = data["Clients"].copy()
    if df.empty:
        st.warning("📄 La feuille 'Clients' est vide.")
        return

    df = _norm_cols(df)

    # ==================== FILTRES ====================
    st.markdown("### 🎯 Filtres")
    col1, col2, col3, col4, col5 = st.columns(5)

    def _opts(dfcol, all_label="(Tous)"):
        if dfcol not in df.columns:
            return [all_label]
        vals = sorted([str(v) for v in df[dfcol].dropna().unique().tolist() if str(v).strip() != ""])
        return [all_label] + vals if vals else [all_label]

    categorie = col1.selectbox("Catégorie", _opts("Catégorie", "(Toutes)"), key="dash_cat")
    souscat = col2.selectbox("Sous-catégorie", _opts("Sous-catégorie", "(Toutes)"), key="dash_souscat")
    visa = col3.selectbox("Visa", _opts("Visa", "(Tous)"), key="dash_visa")
    annee = col4.selectbox("Année", _opts("Année", "(Toutes)"), key="dash_annee")
    mois = col5.selectbox("Mois", _opts("Mois", "(Tous)"), key="dash_mois")

    # Application des filtres
    if categorie != "(Toutes)":
        df = df[df["Catégorie"] == categorie]
    if souscat != "(Toutes)":
        df = df[df["Sous-catégorie"] == souscat]
    if visa != "(Tous)":
        df = df[df["Visa"] == visa]
    if annee != "(Toutes)":
        df = df[df["Année"].astype(str) == str(annee)]
    if mois != "(Tous)":
        df = df[df["Mois"].astype(str) == str(mois)]

    st.markdown("---")

    # ==================== SYNTHÈSE FINANCIÈRE ====================
    st.subheader("📊 Synthèse financière")
    total_honoraire = df["Montant honoraires (US $)"].sum()
    total_autres = df["Autres frais (US $)"].sum()
    total_facture = df["Montant facturé"].sum()
    total_paye = df["Total payé"].sum()
    total_solde = df["Solde restant"].sum()

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Honoraires", f"{total_honoraire:,.0f} $")
    c2.metric("Autres frais", f"{total_autres:,.0f} $")
    c3.metric("Facturé", f"{total_facture:,.0f} $")
    c4.metric("Payé", f"{total_paye:,.0f} $")
    c5.metric("Solde", f"{total_solde:,.0f} $")

    st.markdown("---")

    # ==================== TABLEAU CLIENTS ====================
    st.subheader("📋 Dossiers clients")
    colonnes_aff = [
        "Nom", "Visa", "Catégorie", "Sous-catégorie", "Année", "Mois",
        "Montant honoraires (US $)", "Autres frais (US $)",
        "Montant facturé", "Total payé", "Solde restant"
    ]
    cols_exist = [c for c in colonnes_aff if c in df.columns]
    numeric_cols = df.select_dtypes(include=["number"]).columns
    st.dataframe(
        df[cols_exist].style.format(subset=numeric_cols, formatter="{:,.2f}"),
        use_container_width=True,
        height=420,
    )

    st.markdown("---")

    # ==================== TOP 10 ====================
    st.subheader("🏆 Top 10 des dossiers (par montant facturé)")
    if "Montant facturé" in df.columns:
        top10 = df.nlargest(10, "Montant facturé")[["Nom", "Visa", "Montant facturé", "Total payé", "Solde restant"]]
        st.dataframe(
            top10.style.format(subset=["Montant facturé", "Total payé", "Solde restant"], formatter="{:,.2f}"),
            use_container_width=True,
            height=380,
        )
    else:
        st.info("Colonne 'Montant facturé' absente.")
