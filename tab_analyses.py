import streamlit as st
import pandas as pd

def tab_analyses():
    """Onglet Analyses : filtres + comparatif multi-années (jusqu'à 5) + liste dossiers."""
    st.header("📊 Analyses comparatives")

    # --- Vérif data ---
    if "data_xlsx" not in st.session_state or not st.session_state["data_xlsx"]:
        st.warning("⚠️ Aucune donnée disponible. Chargez d'abord le fichier Excel via l'onglet 📄 Fichiers.")
        return
    data = st.session_state["data_xlsx"]
    if "Clients" not in data:
        st.error("❌ La feuille 'Clients' est absente du fichier Excel.")
        return

    df = data["Clients"].copy()
    if df.empty:
        st.warning("📄 La feuille 'Clients' est vide.")
        return

    # ---------- Helpers ----------
    def _col_first(df_, candidates):
        """Retourne la première colonne présente parmi candidates."""
        for c in candidates:
            if c in df_.columns:
                return c
        return None

    def _to_float(x):
        try:
            s = str(x).replace("\u00A0", "").replace(",", ".").strip()
            return float(s) if s not in ("", "nan", "None") else 0.0
        except Exception:
            return 0.0

    def _fmt_money(v):
        try:
            return f"{float(v):,.2f}".replace(",", " ").replace(".", ",") + " $"
        except Exception:
            return v

    # ---------- Mapping colonnes tolérant accents ----------
    col_cat   = _col_first(df, ["Catégories", "Categories"])
    col_scat  = _col_first(df, ["Sous-catégories", "Sous-categories"])
    col_visa  = _col_first(df, ["Visa"])
    col_mh    = _col_first(df, ["Montant honoraires (US $)", "Montant honoraires (US$)", "Honoraires (US $)"])
    col_autre = _col_first(df, ["Autres frais (US $)", "Autres frais (US$)", "Autres Frais (US $)"])
    col_date  = _col_first(df, ["Date création", "Date de création", "Date", "Date dossier", "Date Création"])

    # Valeurs par défaut si manquants
    if col_mh is None:
        df["Montant honoraires (US $)"] = 0.0
        col_mh = "Montant honoraires (US $)"
    if col_autre is None:
        df["Autres frais (US $)"] = 0.0
        col_autre = "Autres frais (US $)"

    # Nettoyage montants
    df[col_mh] = df[col_mh].map(_to_float)
    df[col_autre] = df[col_autre].map(_to_float)
    df["Montant facturé"] = df[col_mh] + df[col_autre]

    # Date -> Année / Mois
    if col_date is None or col_date not in df.columns:
        st.error("⚠️ Impossible d'identifier la colonne de date (ex. 'Date création').")
        return
    df["_Date_"] = pd.to_datetime(df[col_date], errors="coerce")
    df["Année"] = df["_Date_"].dt.year
    df["Mois"]  = df["_Date_"].dt.month

    # ---------- Filtres ----------
    st.subheader("🎛️ Filtres")

    c1, c2, c3 = st.columns(3)

    # Options filtrage robustes
    cat_opts  = sorted(df[col_cat].dropna().astype(str).unique().tolist()) if col_cat in df else []
    scat_opts = sorted(df[col_scat].dropna().astype(str).unique().tolist()) if col_scat in df else []
    visa_opts = sorted(df[col_visa].dropna().astype(str).unique().tolist()) if col_visa in df else []

    sel_cat  = c1.multiselect("Catégories", options=cat_opts, default=cat_opts if cat_opts else [])
    sel_scat = c2.multiselect("Sous-catégories", options=scat_opts, default=scat_opts if scat_opts else [])
    sel_visa = c3.multiselect("Visa", options=visa_opts, default=visa_opts if visa_opts else [])

    df_f = df.copy()
    if col_cat and sel_cat:
        df_f = df_f[df_f[col_cat].astype(str).isin(sel_cat)]
    if col_scat and sel_scat:
        df_f = df_f[df_f[col_scat].astype(str).isin(sel_scat)]
    if col_visa and sel_visa:
        df_f = df_f[df_f[col_visa].astype(str).isin(sel_visa)]

    # ---------- Choix des années (jusqu'à 5) ----------
    years_avail = sorted([int(y) for y in df_f["Année"].dropna().unique().tolist()])
    if len(years_avail) == 0:
        st.info("Aucune année exploitable après filtres.")
        return

    st.markdown("### 📅 Sélection des années (max 5)")
    sel_years = st.multiselect(
        "Années à comparer",
        options=years_avail,
        default=years_avail[-min(2, len(years_avail)):],  # par défaut: 2 dernières si possible
        max_selections=5
    )
    if not sel_years:
        st.info("Sélectionnez au moins une année.")
        return

    df_f = df_f[df_f["Année"].isin(sel_years)]

    # ---------- Tableau comparatif multi-années ----------
    st.markdown("### 📊 Tableau comparatif (années en colonnes)")

    # Agrégations
    aggr = (
        df_f.groupby("Année")
            .agg({
                "Montant facturé": "sum",
                col_mh: "sum",
                col_autre: "sum",
                "Dossier N": "count"
            })
            .rename(columns={
                "Montant facturé": "Montant facturé",
                col_mh: "Montant honoraires (US $)",
                col_autre: "Autres frais (US $)",
                "Dossier N": "Nombre de dossiers"
            })
            .reindex(sel_years, fill_value=0)
    )

    # Pivot lignes -> indicateurs, colonnes -> années
    pivot = aggr.T  # index: indicateurs / colonnes: années

    # Format monétaire pour 3 premières lignes, brut pour "Nombre de dossiers"
    money_rows = ["Montant facturé", "Montant honoraires (US $)", "Autres frais (US $)"]
    display = pivot.copy()
    for row in money_rows:
        if row in display.index:
            display.loc[row] = display.loc[row].map(_fmt_money)
    # Nombre de dossiers -> entier avec séparateurs d'espace
    if "Nombre de dossiers" in display.index:
        display.loc["Nombre de dossiers"] = display.loc["Nombre de dossiers"].map(
            lambda x: f"{int(x):,}".replace(",", " ")
        )

    st.dataframe(
        display.style.set_table_styles([
            {"selector": "th", "props": [("text-align", "center")]},
            {"selector": "td", "props": [("text-align", "left"), ("padding-left", "12px")]}
        ]),
        use_container_width=True,
        height=320
    )

    st.markdown("---")

    # ---------- Liste comparative des dossiers ----------
    st.markdown("### 🧾 Dossiers par année (Année · Nom · Montant honoraires)")
    list_cols = ["Année", "Nom", col_mh]
    list_cols_existing = [c for c in list_cols if c in df_f.columns]
    if len(list_cols_existing) < 2:
        st.info("Colonnes nécessaires manquantes pour lister les dossiers.")
        return

    df_list = df_f[list_cols_existing].copy()
    # Format montant
    if col_mh in df_list.columns:
        df_list[col_mh] = df_list[col_mh].map(_fmt_money)

    # Tri par année puis par montant décroissant si possible
    sort_cols = [c for c in ["Année", col_mh] if c in df_list.columns]
    ascending = [True, False][:len(sort_cols)]
    if sort_cols:
        # pour trier correctement sur montant, on crée une clé numérique temporaire
        if col_mh in df_f.columns:
            tmp = df_f[[col_mh]].copy()
            tmp["_num_mh_"] = df_f[col_mh].astype(float)
            df_list = df_list.merge(tmp["_num_mh_"], left_index=True, right_index=True, how="left")
            if "Année" in df_list.columns:
                df_list = df_list.sort_values(by=["Année", "_num_mh_"], ascending=[True, False])
            else:
                df_list = df_list.sort_values(by=["_num_mh_"], ascending=[False])
            df_list = df_list.drop(columns=["_num_mh_"])
        else:
            if "Année" in df_list.columns:
                df_list = df_list.sort_values(by=["Année"])

    st.dataframe(
        df_list.style.set_table_styles([
            {"selector": "th", "props": [("text-align", "left")]},
            {"selector": "td", "props": [("text-align", "left"), ("padding-left", "12px")]}
        ]),
        use_container_width=True,
        height=420
    )
