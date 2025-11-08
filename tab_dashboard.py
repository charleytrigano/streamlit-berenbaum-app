import streamlit as st
import pandas as pd
import numpy as np

# ===================== OUTILS =====================

def _best_source(df, candidates):
    for c in candidates:
        if c in df.columns:
            return c
    return None

def _to_datetime_safe(series):
    """Convertit une colonne en datetime sans planter."""
    if series.dtype == "O":
        return pd.to_datetime(series, errors="coerce", dayfirst=True, infer_datetime_format=True)
    if np.issubdtype(series.dtype, np.number):
        return pd.to_datetime(series, errors="coerce", origin="1899-12-30", unit="D")
    return pd.to_datetime(series, errors="coerce")

# ===================== NORMALISATION =====================

def _normalize(df):
    df = df.copy()

    # Colonnes clés possibles
    candidates_date = [
        "Date", "Date d'envoi", "Date création", "Créé le", "Created at", "Created on"
    ]
    candidates_nom = ["Nom", "Client", "Name"]
    candidates_visa = ["Visa", "Type visa", "Visa Type"]
    candidates_cat = ["Catégorie", "Categories", "Categorie", "Type dossier"]
    candidates_souscat = ["Sous-catégorie", "Sous categorie", "Sous-categorie", "Sous type"]

    # Colonnes numériques
    num_cols = [
        "Montant honoraires (US $)", "Autres frais (US $)",
        "Acompte 1", "Acompte 2", "Acompte 3", "Acompte 4"
    ]
    for c in num_cols:
        if c not in df.columns:
            df[c] = 0
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)

    # Création des champs calculés
    df["Montant facturé"] = df["Montant honoraires (US $)"] + df["Autres frais (US $)"]
    df["Total payé"] = df[["Acompte 1", "Acompte 2", "Acompte 3", "Acompte 4"]].sum(axis=1)
    df["Solde restant"] = df["Montant facturé"] - df["Total payé"]

    # Catégories textuelles
    for col, cand in [("Nom", candidates_nom), ("Visa", candidates_visa),
                      ("Catégorie", candidates_cat), ("Sous-catégorie", candidates_souscat)]:
        src = _best_source(df, cand)
        if src:
            df[col] = df[src].astype(str).str.strip().str.title()
        elif col not in df:
            df[col] = ""

    # Année et Mois à partir de la colonne de date
    date_src = _best_source(df, candidates_date)
    if date_src:
        parsed = _to_datetime_safe(df[date_src])
        df["Année"] = parsed.dt.year.fillna(0).astype(int)
        mois_en = parsed.dt.month_name().fillna("") df["Mois"] = mois_en.map({     "January": "Janvier", "February": "Février", "March": "Mars", "April": "Avril",     "May": "Mai", "June": "Juin", "July": "Juillet", "August": "Août",     "September": "Septembre", "October": "Octobre", "November": "Novembre", "December": "Décembre" }).fillna(mois_en)
    else:
        # fallback : colonnes vides mais présentes
        df["Année"] = 0
        df["Mois"] = ""

    # Nettoyage
    df["Année"] = df["Année"].replace(0, np.nan)
    df["Mois"] = df["Mois"].replace("nan", "")

    return df

# ===================== DASHBOARD =====================

def tab_dashboard():
    st.header("📊 Tableau de bord")

    if "data_xlsx" not in st.session_state or not st.session_state["data_xlsx"]:
        st.warning("⚠️ Aucun fichier Excel chargé.")
        return

    data = st.session_state["data_xlsx"]
    if "Clients" not in data:
        st.error("❌ Feuille 'Clients' manquante.")
        return

    df = _normalize(data["Clients"])

    # ========== FILTRES ==========
    st.markdown("### 🎯 Filtres")

    col1, col2, col3, col4, col5 = st.columns(5)
    cat = col1.selectbox("Catégorie", ["(Toutes)"] + sorted(df["Catégorie"].dropna().unique().tolist()))
    souscat = col2.selectbox("Sous-catégorie", ["(Toutes)"] + sorted(df["Sous-catégorie"].dropna().unique().tolist()))
    visa = col3.selectbox("Visa", ["(Tous)"] + sorted(df["Visa"].dropna().unique().tolist()))
    annee = col4.selectbox("Année", ["(Toutes)"] + sorted(df["Année"].dropna().unique().astype(int).astype(str).tolist()))
    mois = col5.selectbox("Mois", ["(Tous)"] + sorted([m for m in df["Mois"].dropna().unique().tolist() if m]))

    # Application
    dff = df.copy()
    if cat != "(Toutes)":
        dff = dff[dff["Catégorie"] == cat]
    if souscat != "(Toutes)":
        dff = dff[dff["Sous-catégorie"] == souscat]
    if visa != "(Tous)":
        dff = dff[dff["Visa"] == visa]
    if annee != "(Toutes)":
        dff = dff[dff["Année"].astype(str) == annee]
    if mois != "(Tous)":
        dff = dff[dff["Mois"].astype(str) == mois]

    st.markdown("---")

    # ========== KPI ==========
    st.subheader("📈 Synthèse financière")
    st.markdown("""
        <style>
        [data-testid="stMetricValue"] { font-size:18px; }
        [data-testid="stMetricLabel"] { font-size:13px; }
        </style>
    """, unsafe_allow_html=True)

    c0, c1, c2, c3, c4, c5 = st.columns(6)
    c0.metric("📁 Dossiers", f"{len(dff)}")
    c1.metric("Honoraires", f"{dff['Montant honoraires (US $)'].sum():,.0f} $")
    c2.metric("Autres frais", f"{dff['Autres frais (US $)'].sum():,.0f} $")
    c3.metric("Facturé", f"{dff['Montant facturé'].sum():,.0f} $")
    c4.metric("Payé", f"{dff['Total payé'].sum():,.0f} $")
    c5.metric("Solde", f"{dff['Solde restant'].sum():,.0f} $")

    st.markdown("---")

    # ========== COMPARATIF ==========
    st.markdown("### 🔄 Comparatif entre deux périodes")
    colA, colB, colC, colD = st.columns(4)
    a1 = colA.selectbox("Année 1", ["(Toutes)"] + sorted(df["Année"].dropna().astype(int).astype(str).tolist()))
    m1 = colB.selectbox("Mois 1", ["(Tous)"] + sorted(df["Mois"].dropna().unique().tolist()))
    a2 = colC.selectbox("Année 2", ["(Toutes)"] + sorted(df["Année"].dropna().astype(int).astype(str).tolist()))
    m2 = colD.selectbox("Mois 2", ["(Tous)"] + sorted(df["Mois"].dropna().unique().tolist()))

    if a1 != "(Toutes)" and a2 != "(Toutes)":
        d1 = df[(df["Année"].astype(str) == a1) & (df["Mois"] == m1)]
        d2 = df[(df["Année"].astype(str) == a2) & (df["Mois"] == m2)]
        v1, v2 = d1["Montant facturé"].sum(), d2["Montant facturé"].sum()
        delta = v2 - v1
        pct = (delta / v1 * 100) if v1 else 0

        st.dataframe(pd.DataFrame({
            "Période": [f"{m1} {a1}", f"{m2} {a2}", "Évolution"],
            "Montant facturé ($)": [v1, v2, delta],
            "Variation (%)": ["", "", f"{pct:+.1f}%"]
        }), use_container_width=True, height=150)
    else:
        st.caption("Sélectionnez deux périodes pour comparer.")

    st.markdown("---")

    # ========== TABLEAU ==========
    st.subheader("📋 Dossiers clients")
    cols = [
        "Nom", "Visa", "Catégorie", "Sous-catégorie", "Année", "Mois",
        "Montant honoraires (US $)", "Autres frais (US $)",
        "Montant facturé", "Total payé", "Solde restant"
    ]
    st.dataframe(dff[cols], use_container_width=True, height=400)

    # ========== TOP 10 ==========
    st.subheader("🏆 Top 10 des dossiers (par montant facturé)")
    top10 = dff.nlargest(10, "Montant facturé")[["Nom", "Visa", "Montant facturé", "Total payé", "Solde restant"]]
    st.dataframe(top10, use_container_width=True, height=300)

