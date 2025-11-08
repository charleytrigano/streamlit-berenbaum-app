import streamlit as st
import pandas as pd

# ===================== FONCTIONS UTILES =====================

def _lower_map(columns):
    return {str(c).strip().lower(): c for c in columns}

def _find_present(df, candidates):
    lmap = _lower_map(df.columns)
    return [lmap[c.lower()] for c in candidates if c.lower() in lmap]

def _best_source(df, candidates):
    found = _find_present(df, candidates)
    if not found:
        return None
    if len(found) == 1:
        return found[0]
    counts = [(c, df[c].notna().sum()) for c in found]
    counts.sort(key=lambda x: x[1], reverse=True)
    return counts[0][0]

def _ensure_std_col(df, std_name, candidates, transform=None, default_value=""):
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
        "Visa": ["Visa", "Type visa", "visa"],
        "Catégorie": ["Catégorie", "Categories", "Categorie", "category", "Type dossier"],
        "Sous-catégorie": ["Sous-catégorie", "Sous categorie", "Sous-categorie", "Sous type"],
        "Année": ["Année", "Annee", "Year"],
        "Mois": ["Mois", "mois", "Month"],
        "Nom": ["Nom", "Client", "name"],
        "_date_probe_": ["Date", "date", "Date d'envoi", "Created at"],
    }

    NUMS = [
        "Montant honoraires (US $)", "Autres frais (US $)",
        "Acompte 1", "Acompte 2", "Acompte 3", "Acompte 4"
    ]

    df = _ensure_std_col(df, "Nom", CAND["Nom"])
    df = _ensure_std_col(df, "Visa", CAND["Visa"], transform=lambda s: s.str.title())
    df = _ensure_std_col(df, "Catégorie", CAND["Catégorie"], transform=lambda s: s.str.title())
    df = _ensure_std_col(df, "Sous-catégorie", CAND["Sous-catégorie"], transform=lambda s: s.str.title())

    for col in NUMS:
        if col not in df.columns:
            df[col] = 0
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    df["Montant facturé"] = df["Montant honoraires (US $)"] + df["Autres frais (US $)"]
    df["Total payé"] = df[["Acompte 1", "Acompte 2", "Acompte 3", "Acompte 4"]].sum(axis=1)
    df["Solde restant"] = df["Montant facturé"] - df["Total payé"]

    for c in ["Catégorie", "Sous-catégorie", "Visa"]:
        df[c] = df[c].astype(str).str.strip().str.title()

    return df

def _opts_from(df, col, all_label="(Tous)"):
    if col not in df.columns:
        return [all_label]
    vals = df[col].dropna().astype(str).map(lambda x: x.strip()).replace({"None": "", "nan": ""})
    vals = sorted([v for v in vals.unique().tolist() if v])
    return [all_label] + vals if vals else [all_label]

# ===================== TABLEAU DE BORD =====================

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

    categorie = col1.selectbox("Catégorie", _opts_from(df, "Catégorie", "(Toutes)"))
    souscat   = col2.selectbox("Sous-catégorie", _opts_from(df, "Sous-catégorie", "(Toutes)"))
    visa      = col3.selectbox("Visa", _opts_from(df, "Visa", "(Tous)"))
    annee     = col4.selectbox("Année", _opts_from(df, "Année", "(Toutes)"))
    mois      = col5.selectbox("Mois", _opts_from(df, "Mois", "(Tous)"))

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

    # ======= KPI (taille réduite) =======
    st.subheader("📈 Synthèse financière")
    total_honoraire = df["Montant honoraires (US $)"].sum()
    total_autres = df["Autres frais (US $)"].sum()
    total_facture = df["Montant facturé"].sum()
    total_paye = df["Total payé"].sum()
    total_solde = df["Solde restant"].sum()
    nb_dossiers = len(df)

    kpi_style = """
    <style>
    [data-testid="stMetricValue"] { font-size: 18px; }
    [data-testid="stMetricLabel"] { font-size: 14px; }
    </style>
    """
    st.markdown(kpi_style, unsafe_allow_html=True)

    c0, c1, c2, c3, c4, c5 = st.columns(6)
    c0.metric("📁 Dossiers", f"{nb_dossiers:,}")
    c1.metric("Honoraires", f"{total_honoraire:,.0f} $")
    c2.metric("Autres frais", f"{total_autres:,.0f} $")
    c3.metric("Facturé", f"{total_facture:,.0f} $")
    c4.metric("Payé", f"{total_paye:,.0f} $")
    c5.metric("Solde", f"{total_solde:,.0f} $")

    st.markdown("---")

    # ======= Comparatif simple entre deux périodes =======
    st.markdown("### 🔄 Comparatif entre deux périodes")

    colA, colB, colC, colD = st.columns(4)
    annee1 = colA.selectbox("Année 1", _opts_from(df, "Année", "(Toutes)"), key="a1")
    mois1  = colB.selectbox("Mois 1", _opts_from(df, "Mois", "(Tous)"), key="m1")
    annee2 = colC.selectbox("Année 2", _opts_from(df, "Année", "(Toutes)"), key="a2")
    mois2  = colD.selectbox("Mois 2", _opts_from(df, "Mois", "(Tous)"), key="m2")

    if annee1 != "(Toutes)" and annee2 != "(Toutes)":
        d1 = df[(df["Année"].astype(str) == str(annee1)) & (df["Mois"].astype(str) == str(mois1))]
        d2 = df[(df["Année"].astype(str) == str(annee2)) & (df["Mois"].astype(str) == str(mois2))]

        t1 = d1["Montant facturé"].sum() if not d1.empty else 0
        t2 = d2["Montant facturé"].sum() if not d2.empty else 0
        delta = t2 - t1
        pct = (delta / t1 * 100) if t1 else 0

        data_cmp = pd.DataFrame({
            "Période": [f"{mois1} {annee1}", f"{mois2} {annee2}", "Évolution"],
            "Montant facturé ($)": [t1, t2, delta],
            "Variation (%)": ["", "", f"{pct:+.1f}%"]
        })
        st.dataframe(data_cmp, use_container_width=True, height=160)
    else:
        st.caption("Sélectionnez deux périodes pour afficher le comparatif.")

    st.markdown("---")

    # ======= Tableau principal =======
    st.subheader("📋 Dossiers clients")
    colonnes_aff = [
        "Nom", "Visa", "Catégorie", "Sous-catégorie", "Année", "Mois",
        "Montant honoraires (US $)", "Autres frais (US $)",
        "Montant facturé", "Total payé", "Solde restant"
    ]
    cols_exist = [c for c in colonnes_aff if c in df.columns]
    numeric_cols = [c for c in cols_exist if pd.api.types.is_numeric_dtype(df[c])]
    st.dataframe(
        df[cols_exist].style.format(subset=numeric_cols, formatter="{:,.2f}"),
        use_container_width=True,
        height=400,
    )

    # ======= Top 10 =======
    st.subheader("🏆 Top 10 des dossiers (par montant facturé)")
    if "Montant facturé" in df.columns:
        top10 = df.nlargest(10, "Montant facturé")[["Nom", "Visa", "Montant facturé", "Total payé", "Solde restant"]]
        st.dataframe(
            top10.style.format(subset=["Montant facturé", "Total payé", "Solde restant"], formatter="{:,.2f}"),
            use_container_width=True,
            height=300,
        )
