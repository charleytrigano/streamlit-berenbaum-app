import streamlit as st
import pandas as pd
from datetime import datetime

# ===================== UTILITAIRES =====================

def _lower_map(columns):
    """Crée un dictionnaire {lowercase: nom_original} pour les colonnes."""
    return {str(c).strip().lower(): c for c in columns}

def _find_present(df, candidates):
    """Renvoie les colonnes présentes parmi une liste de candidats."""
    lmap = _lower_map(df.columns)
    return [lmap[c.lower()] for c in candidates if c.lower() in lmap]

def _best_source(df, candidates):
    """Choisit la colonne la plus remplie parmi les candidats."""
    found = _find_present(df, candidates)
    if not found:
        return None
    if len(found) == 1:
        return found[0]
    counts = [(c, df[c].notna().sum()) for c in found]
    counts.sort(key=lambda x: x[1], reverse=True)
    return counts[0][0]

def _ensure_std_col(df, std_name, candidates, transform=None, default_value=""):
    """Crée une colonne standard à partir de candidats existants."""
    if std_name in df.columns:
        s = df[std_name]
    else:
        src = _best_source(df, candidates)
        s = df[src] if src else pd.Series([default_value] * len(df), index=df.index)
    s = s.copy()
    if s.dtype == "O":
        s = s.astype(str).str.strip()
    if transform:
        s = transform(s)
    df[std_name] = s
    return df

# ===================== NORMALISATION =====================

def _norm_cols(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    CAND = {
        "Visa": ["Visa", "Type visa", "type visa", "visa"],
        "Catégorie": [
            "Catégorie", "Categories", "Categorie", "category", "Category",
            "Type dossier", "type dossier", "type_dossier", "type de dossier"
        ],
        "Sous-catégorie": [
            "Sous-catégorie", "Sous categorie", "Sous-categorie",
            "subcategory", "Sous type", "Sous-type", "sous type", "sous-type"
        ],
        "Année": ["Année", "Annee", "année", "annee", "Year", "year"],
        "Mois": ["Mois", "mois", "Month", "month"],
        "Nom": ["Nom", "Client", "name", "full name", "Full Name"],
        "_date_probe_": [
            "Date", "date", "Date création", "date création",
            "Date d'envoi", "date d'envoi", "Créé le", "créé le",
            "Created at", "created at", "Created_on", "created_on"
        ],
    }

    NUMS = [
        "Montant honoraires (US $)", "Autres frais (US $)",
        "Acompte 1", "Acompte 2", "Acompte 3", "Acompte 4"
    ]

    # Colonnes de texte principales
    df = _ensure_std_col(df, "Nom", CAND["Nom"])
    df = _ensure_std_col(df, "Visa", CAND["Visa"], transform=lambda s: s.str.title())
    df = _ensure_std_col(df, "Catégorie", CAND["Catégorie"], transform=lambda s: s.str.title())
    df = _ensure_std_col(df, "Sous-catégorie", CAND["Sous-catégorie"], transform=lambda s: s.str.title())

    # Colonnes numériques
    for col in NUMS:
        if col not in df.columns:
            df[col] = 0
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # Calculs financiers
    df["Montant facturé"] = df["Montant honoraires (US $)"] + df["Autres frais (US $)"]
    df["Total payé"] = df[["Acompte 1", "Acompte 2", "Acompte 3", "Acompte 4"]].sum(axis=1)
    df["Solde restant"] = df["Montant facturé"] - df["Total payé"]

    # Année / Mois
    MONTHS_FR = ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
                 "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"]

    have_year = "Année" in df.columns and df["Année"].notna().any()
    have_month = "Mois" in df.columns and df["Mois"].notna().any()

    if not have_year or not have_month:
        probe_src = _best_source(df, CAND["_date_probe_"])
        if probe_src is not None:
            parsed = pd.to_datetime(df[probe_src], errors="coerce", dayfirst=True, infer_datetime_format=True)
            if not have_year:
                df["Année"] = parsed.dt.year
            if not have_month:
                df["Mois"] = parsed.dt.month.map(lambda x: MONTHS_FR[int(x)-1] if pd.notna(x) and 1 <= int(x) <= 12 else "")
        else:
            if "Année" not in df.columns:
                df["Année"] = ""
            if "Mois" not in df.columns:
                df["Mois"] = ""

    for c in ["Catégorie", "Sous-catégorie", "Visa"]:
        df[c] = df[c].astype(str).str.strip().str.title()

    return df

# ===================== DASHBOARD PRINCIPAL =====================

def _opts_from(df, col, all_label="(Tous)"):
    if col not in df.columns:
        return [all_label]
    vals = df[col].dropna().astype(str).map(lambda x: x.strip()).replace({"None": "", "nan": ""})
    vals = sorted([v for v in vals.unique().tolist() if v])
    return [all_label] + vals if vals else [all_label]

def tab_dashboard():
    st.header("📊 Tableau de bord")

    if "data_xlsx" not in st.session_state or not st.session_state["data_xlsx"]:
        st.warning("⚠️ Aucune donnée disponible. Chargez d'abord le fichier Excel via l'onglet '📄 Fichiers'.")
        return

    data = st.session_state["data_xlsx"]
    if "Clients" not in data:
        st.error("❌ La feuille 'Clients' est absente du fichier Excel.")
        return

    df_raw = data["Clients"].copy()
    if df_raw.empty:
        st.warning("📄 La feuille 'Clients' est vide.")
        return

    df = _norm_cols(df_raw)

    # ======= Filtres =======
    st.markdown("### 🎯 Filtres")
    col1, col2, col3, col4, col5 = st.columns(5)

    categorie = col1.selectbox("Catégorie", _opts_from(df, "Catégorie", "(Toutes)"), key="dash_cat")
    souscat   = col2.selectbox("Sous-catégorie", _opts_from(df, "Sous-catégorie", "(Toutes)"), key="dash_souscat")
    visa      = col3.selectbox("Visa", _opts_from(df, "Visa", "(Tous)"), key="dash_visa")
    annee     = col4.selectbox("Année", _opts_from(df, "Année", "(Toutes)"), key="dash_annee")
    mois      = col5.selectbox("Mois", _opts_from(df, "Mois", "(Tous)"), key="dash_mois")

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

    # ======= KPI =======
    st.subheader("📊 Synthèse financière")
    total_honoraire = df["Montant honoraires (US $)"].sum()
    total_autres = df["Autres frais (US $)"].sum()
    total_facture = df["Montant facturé"].sum()
    total_paye = df["Total payé"].sum()
    total_solde = df["Solde restant"].sum()
    nb_dossiers = len(df)

    c0, c1, c2, c3, c4, c5 = st.columns(6)
    c0.metric("📁 Dossiers", f"{nb_dossiers:,}")
    c1.metric("Honoraires", f"{total_honoraire:,.0f} $")
    c2.metric("Autres frais", f"{total_autres:,.0f} $")
    c3.metric("Facturé", f"{total_facture:,.0f} $")
    c4.metric("Payé", f"{total_paye:,.0f} $")
    c5.metric("Solde", f"{total_solde:,.0f} $")

    st.markdown("---")

    # ======= Tableau principal =======
    st.subheader("📋 Dossiers clients")
    colonnes_aff = [
        "Nom", "Visa", "Catégorie", "Sous-catégorie", "Année", "Mois",
        "Montant honoraires (US $)", "Autres frais (US $)",
        "Montant facturé", "Total payé", "Solde restant"
    ]
    cols_exist = [c for c in colonnes_aff if c in df.columns]
    df_view = df[cols_exist].copy()
    numeric_cols = [c for c in df_view.columns if pd.api.types.is_numeric_dtype(df_view[c])]
    st.dataframe(
        df_view.style.format(subset=numeric_cols, formatter="{:,.2f}"),
        use_container_width=True,
        height=420,
    )

    st.markdown("---")

    # ======= Top 10 =======
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
