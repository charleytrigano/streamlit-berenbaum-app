import streamlit as st
import pandas as pd
from datetime import datetime

# ===================== Utilities robustes =====================

def _lower_map(columns):
    """Mappe lower()->nom original des colonnes pour des recherches insensibles à la casse/espaces."""
    return {str(c).strip().lower(): c for c in columns}

def _find_present(df, name_candidates):
    """Retourne la liste (dans l'ordre) des noms de colonnes réellement présentes
    parmi les candidats, en respectant la casse d'origine du DataFrame."""
    lmap = _lower_map(df.columns)
    found = []
    for cand in name_candidates:
        key = str(cand).strip().lower()
        if key in lmap:
            found.append(lmap[key])
    return found

def _best_source(df, name_candidates):
    """Parmi plusieurs candidats présents, choisit la colonne ayant le plus de valeurs non nulles."""
    present = _find_present(df, name_candidates)
    if not present:
        return None
    if len(present) == 1:
        return present[0]
    # Choisir la plus 'remplie'
    counts = [(c, df[c].notna().sum()) for c in present]
    counts.sort(key=lambda x: x[1], reverse=True)
    return counts[0][0]

def _ensure_std_col(df, std_name, candidates, transform=None, default_value=""):
    """Crée/garantit une colonne standardisée 'std_name' en copiant la meilleure source disponible.
    Si aucune source, crée une colonne vide. Optionnellement applique transform(série)->série."""
    if std_name in df.columns:
        s = df[std_name]
    else:
        src = _best_source(df, candidates)
        if src is not None:
            s = df[src]
        else:
            s = pd.Series([default_value] * len(df), index=df.index)
    s = s.copy()
    # Normalisation basique des chaînes
    if s.dtype == "O":
        s = s.astype(str).str.strip()
    if transform is not None:
        s = transform(s)
    df[std_name] = s
    return df

def _norm_cols(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # Candidats pour chaque colonne standard
    CAND = {
        "Visa": ["Visa", "Type visa", "type visa", "type_de_visa", "type-visa", "visa"],
        "Catégorie": ["Catégorie", "Categorie", "category", "Category", "Type dossier", "type dossier", "type_dossier"],
        "Sous-catégorie": [
            "Sous-catégorie", "Sous categorie", "Sous-categorie",
            "subcategory", "Sous type", "Sous-type", "sous type", "sous-type"
        ],
        "Année": ["Année", "Annee", "année", "annee", "Year", "year"],
        "Mois": ["Mois", "mois", "Month", "month"],
        "Nom": ["Nom", "Client", "name", "full name", "Full Name"],
        "_date_probe_": ["Date", "date", "Date création", "date création", "Date d'envoi", "date d'envoi",
                         "Créé le", "créé le", "Created at", "created at", "Created_on", "created_on"]
    }

    # Colonnes numériques (on fera coalesce si absentes)
    NUMS = ["Montant honoraires (US $)", "Autres frais (US $)", "Acompte 1", "Acompte 2", "Acompte 3", "Acompte 4"]

    # 1) Garantir les colonnes de libellés via coalescing robuste
    df = _ensure_std_col(df, "Nom", CAND["Nom"])
    df = _ensure_std_col(df, "Visa", CAND["Visa"], transform=lambda s: s.str.title())
    df = _ensure_std_col(df, "Catégorie", CAND["Catégorie"], transform=lambda s: s.str.title())
    df = _ensure_std_col(df, "Sous-catégorie", CAND["Sous-catégorie"], transform=lambda s: s.str.title())

    # 2) Colonnes numériques
    for col in NUMS:
        if col not in df.columns:
            df[col] = 0
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # 3) Calculs financiers
    df["Montant facturé"] = df["Montant honoraires (US $)"] + df["Autres frais (US $)"]
    df["Total payé"] = df[["Acompte 1", "Acompte 2", "Acompte 3", "Acompte 4"]].sum(axis=1)
    df["Solde restant"] = df["Montant facturé"] - df["Total payé"]

    # 4) Année / Mois : déduction fiable si manquantes
    MONTHS_FR = ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
                 "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"]

    have_year = "Année" in df.columns and df["Année"].notna().any()
    have_month = "Mois" in df.columns and df["Mois"].notna().any()

    if not have_year or not have_month:
        # Trouver la meilleure colonne de date
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

    # Harmoniser types
    if "Année" in df.columns:
        # laisser mixte possible, on filtre en str plus tard
        pass
    if "Mois" in df.columns:
        df["Mois"] = df["Mois"].astype(str).str.strip()

    return df

def _opts_from(df, col, all_label="(Tous)"):
    """Construit les options non vides et triées pour un filtre donné."""
    if col not in df.columns:
        return [all_label]
    vals = df[col].dropna().astype(str).map(lambda x: x.strip()).replace({"None": "", "nan": ""})
    vals = sorted([v for v in vals.unique().tolist() if v != ""])
    return [all_label] + vals if vals else [all_label]

# ===================== Onglet Dashboard =====================

def tab_dashboard():
    """Tableau de bord principal - filtres Catégorie/Sous-catégorie robustes + KPI nombre de dossiers."""
    st.header("📊 Tableau de bord")

    # Données chargées ?
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

    # Normalisation + coalescing des colonnes (clé de la correction)
    df = _norm_cols(df_raw)

    # ================= Filtres =================
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

    # ================= KPI =================
    st.subheader("📊 Synthèse financière")
    total_honoraire = df["Montant honoraires (US $)"].sum()
    total_autres    = df["Autres frais (US $)"].sum()
    total_facture   = df["Montant facturé"].sum()
    total_paye      = df["Total payé"].sum()
    total_solde     = df["Solde restant"].sum()
    nb_dossiers     = len(df)

    c0, c1, c2, c3, c4, c5 = st.columns(6)
    c0.metric("📁 Dossiers", f"{nb_dossiers:,}")
    c1.metric("Honoraires", f"{total_honoraire:,.0f} $")
    c2.metric("Autres frais", f"{total_autres:,.0f} $")
    c3.metric("Facturé", f"{total_facture:,.0f} $")
    c4.metric("Payé", f"{total_paye:,.0f} $")
    c5.metric("Solde", f"{total_solde:,.0f} $")

    st.markdown("---")

    # ================= Tableau =================
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

    # ================= Top 10 =================
    st.subheader("🏆 Top 10 des dossiers (par montant facturé)")
    if "Montant facturé" in df.columns:
        top10 = df.nlargest(10, "Montant facturé")[
            [c for c in ["Nom", "Visa", "Montant facturé", "Total payé", "Solde restant"] if c in df.columns]
        ]
        st.dataframe(
            top10.style.format(subset=[c for c in ["Montant facturé", "Total payé", "Solde restant"] if c in top10.columns],
                               formatter="{:,.2f}"),
            use_container_width=True,
            height=380,
        )
    else:
        st.info("Colonne 'Montant facturé' absente.")
