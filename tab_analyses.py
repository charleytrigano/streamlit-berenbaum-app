import streamlit as st
import pandas as pd

def tab_analyses():
    """Onglet Analyses : comparaison par périodes et filtres multi-critères."""

    st.header("📊 Analyses comparatives")

    # Vérifie si les données Excel sont chargées
    if "data_xlsx" not in st.session_state or not st.session_state["data_xlsx"]:
        st.warning("⚠️ Aucune donnée disponible. Chargez d'abord le fichier Excel via l'onglet 📄 Fichiers.")
        return

    data = st.session_state["data_xlsx"]

    # Vérifie la présence de la feuille Clients
    if "Clients" not in data:
        st.error("❌ La feuille 'Clients' est absente du fichier Excel.")
        return

    df = data["Clients"].copy()
    if df.empty:
        st.warning("📄 La feuille 'Clients' est vide.")
        return

    # === Nettoyage ===
    def _to_float(x):
        try:
            s = str(x).replace(",", ".").replace("\u00A0", "").strip()
            return float(s) if s not in ["", "nan", "None"] else 0.0
        except:
            return 0.0

    if "Montant honoraires (US $)" not in df.columns:
        st.error("La colonne 'Montant honoraires (US $)' est manquante.")
        return

    for col in ["Montant honoraires (US $)", "Autres frais (US $)"]:
        if col in df.columns:
            df[col] = df[col].map(_to_float)
        else:
            df[col] = 0.0

    df["Montant facturé"] = df["Montant honoraires (US $)"] + df["Autres frais (US $)"]

    # Extraction de la colonne de date
    date_col = None
    for c in df.columns:
        if "date" in c.lower() and "creation" in c.lower():
            date_col = c
            break
    if not date_col:
        date_col = "Date"
    if date_col not in df.columns:
        st.error("⚠️ Impossible de trouver une colonne de date.")
        return

    df["Date"] = pd.to_datetime(df[date_col], errors="coerce")
    df["Année"] = df["Date"].dt.year
    df["Mois"] = df["Date"].dt.month

    # === Filtres ===
    st.markdown("### 🔍 Filtres d’analyse")

    col1, col2, col3 = st.columns(3)

    categories = df["Catégories"].dropna().unique().tolist() if "Catégories" in df else []
    souscat = df["Sous-catégories"].dropna().unique().tolist() if "Sous-catégories" in df else []
    visas = df["Visa"].dropna().unique().tolist() if "Visa" in df else []

    selected_cat = col1.multiselect("Catégories", options=categories, default=categories)
    selected_souscat = col2.multiselect("Sous-catégories", options=souscat, default=souscat)
    selected_visa = col3.multiselect("Visa", options=visas, default=visas)

    df_filtered = df.copy()
    if "Catégories" in df and selected_cat:
        df_filtered = df_filtered[df_filtered["Catégories"].isin(selected_cat)]
    if "Sous-catégories" in df and selected_souscat:
        df_filtered = df_filtered[df_filtered["Sous-catégories"].isin(selected_souscat)]
    if "Visa" in df and selected_visa:
        df_filtered = df_filtered[df_filtered["Visa"].isin(selected_visa)]

    # === Comparatif entre années ===
    st.markdown("### 📅 Comparatif entre années")

    available_years = sorted(df_filtered["Année"].dropna().unique().tolist())
    if len(available_years) < 2:
        st.info("Pas assez d'années pour comparer.")
        return

    colA, colB = st.columns(2)
    year1 = colA.selectbox("Période 1", options=available_years, index=0)
    year2 = colB.selectbox("Période 2", options=available_years, index=len(available_years)-1)

    df_compare = (
        df_filtered.groupby("Année")[["Montant facturé", "Montant honoraires (US $)", "Autres frais (US $)"]]
        .sum()
        .reset_index()
    )

    # Table pivot avec les années en colonnes
    pivot = df_compare.set_index("Année").T

    def _fmt_money(v):
        try:
            return f"{v:,.2f}".replace(",", " ").replace(".", ",") + " $"
        except:
            return v

    pivot = pivot.applymap(_fmt_money)

    st.markdown("### 📊 Tableau comparatif")
    st.dataframe(
        pivot.style.set_table_styles([
            {"selector": "th", "props": [("text-align", "center")]},
            {"selector": "td", "props": [("text-align", "left"), ("padding-left", "12px")]}
        ]),
        use_container_width=True,
        height=300
    )

    # Différence absolue et relative
    if year1 in df_compare["Année"].values and year2 in df_compare["Année"].values:
        y1 = df_compare[df_compare["Année"] == year1].iloc[0]
        y2 = df_compare[df_compare["Année"] == year2].iloc[0]
        delta_facture = y2["Montant facturé"] - y1["Montant facturé"]

        st.markdown("---")
        c1, c2 = st.columns(2)
        c1.metric(f"Montant {year1}", _fmt_money(y1['Montant facturé']))
        c2.metric(f"Montant {year2}", _fmt_money(y2['Montant facturé']), delta=f"{delta_facture:,.2f}".replace(",", " ").replace(".", ",") + " $")

    st.markdown("---")
    st.markdown("### 🧾 Top 10 des dossiers par montant facturé")
    top10 = df_filtered.sort_values("Montant facturé", ascending=False).head(10)[
        ["Dossier N", "Nom", "Montant facturé", "Année"]
    ].copy()
    top10["Montant facturé"] = top10["Montant facturé"].map(_fmt_money)
    st.dataframe(
        top10.style.set_table_styles([
            {"selector": "th", "props": [("text-align", "left")]},
            {"selector": "td", "props": [("text-align", "left"), ("padding-left", "12px")]}
        ]),
        use_container_width=True,
        height=350
    )
