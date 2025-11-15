import streamlit as st
import pandas as pd
import unicodedata as _ud

def tab_analyses():
    """Onglet Analyses : filtres + comparatif multi-années (jusqu'à 5) + comparaison libre de deux périodes."""
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

    def _norm_txt(s):
        if s is None:
            return ""
        s = str(s).strip()
        s = _ud.normalize("NFKD", s)
        s = "".join(ch for ch in s if not _ud.combining(ch))
        s = s.lower().replace("\u00A0", " ").strip()
        s = " ".join(s.split())
        return s

    # ---------- Mapping colonnes tolérant accents ----------
    col_cat   = _col_first(df, ["Catégories", "Categories", "Categorie", "Catégorie"])
    col_scat  = _col_first(df, ["Sous-catégories", "Sous-categories", "Sous-categorie", "Sous-catégorie", "Sous catégorie", "Sous categorie"])
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

    # ---------- Colonnes normalisées pour les filtres ----------
    if col_cat:
        df["_cat_norm_"] = df[col_cat].map(_norm_txt)
    else:
        df["_cat_norm_"] = ""
    if col_scat:
        df["_scat_norm_"] = df[col_scat].map(_norm_txt)
    else:
        df["_scat_norm_"] = ""
    if col_visa:
        df["_visa_norm_"] = df[col_visa].map(_norm_txt)
    else:
        df["_visa_norm_"] = ""

    # ---------- Filtres (robustes aux accents/casse/espaces) ----------
    st.subheader("🎛️ Filtres")
    c1, c2, c3 = st.columns(3)

    cat_opts_display  = sorted(df[col_cat].dropna().astype(str).unique().tolist()) if col_cat in df else []
    scat_opts_display = sorted(df[col_scat].dropna().astype(str).unique().tolist()) if col_scat in df else []
    visa_opts_display = sorted(df[col_visa].dropna().astype(str).unique().tolist()) if col_visa in df else []

    sel_cat_display  = c1.multiselect("Catégories", options=cat_opts_display, default=cat_opts_display if cat_opts_display else [])
    sel_scat_display = c2.multiselect("Sous-catégories", options=scat_opts_display, default=scat_opts_display if scat_opts_display else [])
    sel_visa_display = c3.multiselect("Visa", options=visa_opts_display, default=visa_opts_display if visa_opts_display else [])

    sel_cat_norm  = set(_norm_txt(x) for x in sel_cat_display) if sel_cat_display else set()
    sel_scat_norm = set(_norm_txt(x) for x in sel_scat_display) if sel_scat_display else set()
    sel_visa_norm = set(_norm_txt(x) for x in sel_visa_display) if sel_visa_display else set()

    df_f = df.copy()
    if sel_cat_norm:
        df_f = df_f[df_f["_cat_norm_"].isin(sel_cat_norm)]
    if sel_scat_norm:
        df_f = df_f[df_f["_scat_norm_"].isin(sel_scat_norm)]
    if sel_visa_norm:
        df_f = df_f[df_f["_visa_norm_"].isin(sel_visa_norm)]

    # ---------- Sélection du type de comparaison ----------
    st.markdown("### 🔀 Type de comparaison")
    compare_choice = st.radio(
        "Choisissez le mode de comparaison",
        options=["Comparaison multi-années", "Comparaison de deux périodes"],
        index=0
    )

    # ---------- Comparaison MULTI-ANNÉES ----------
    if compare_choice == "Comparaison multi-années":
        years_avail = sorted([int(y) for y in df_f["Année"].dropna().unique().tolist()])
        if len(years_avail) == 0:
            st.info("Aucune année exploitable après filtres.")
            return

        st.markdown("#### 📅 Sélection des années (max 5)")
        default_years = years_avail[-min(2, len(years_avail)):]  # 2 dernières si possible
        sel_years = st.multiselect(
            "Années à comparer",
            options=years_avail,
            default=default_years,
            max_selections=5
        )
        if not sel_years:
            st.info("Sélectionnez au moins une année.")
            return

        df_multi = df_f[df_f["Année"].isin(sel_years)]
        aggr = (
            df_multi.groupby("Année")
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

        pivot = aggr.T  # indicateurs x années

        money_rows = ["Montant facturé", "Montant honoraires (US $)", "Autres frais (US $)"]
        display = pivot.copy()
        for row in money_rows:
            if row in display.index:
                display.loc[row] = display.loc[row].map(_fmt_money)

        if "Nombre de dossiers" in display.index:
            display.loc["Nombre de dossiers"] = display.loc["Nombre de dossiers"].map(lambda x: f"{int(x):,}".replace(",", " "))

        st.markdown("#### 📊 Tableau comparatif (années en colonnes)")
        st.dataframe(
            display.style.set_table_styles([
                {"selector": "th", "props": [("text-align", "center")]},
                {"selector": "td", "props": [("text-align", "left"), ("padding-left", "12px")] }
            ]),
            use_container_width=True,
            height=320
        )

        # Liste dossiers
        st.markdown("---")
        st.markdown("#### 🧾 Dossiers par année")
        list_cols = ["Année", "Nom", col_mh]
        list_cols_existing = [c for c in list_cols if c in df_multi.columns]
        if len(list_cols_existing) < 2:
            st.info("Colonnes nécessaires manquantes pour lister les dossiers.")
            return

        df_list = df_multi[list_cols_existing].copy()
        if col_mh in df_list.columns:
            df_list[col_mh] = df_list[col_mh].map(_fmt_money)

        if "Année" in df_list.columns and col_mh in df_multi.columns:
            nums = df_multi[col_mh].astype(float)
            df_list = df_list.join(nums.rename("_num_mh_"))
            df_list = df_list.sort_values(by=["Année", "_num_mh_"], ascending=[True, False]).drop(columns=["_num_mh_"])
        elif "Année" in df_list.columns:
            df_list = df_list.sort_values(by=["Année"])

        st.dataframe(
            df_list.style.set_table_styles([
                {"selector": "th", "props": [("text-align", "left")]},
                {"selector": "td", "props": [("text-align", "left"), ("padding-left", "12px")] }
            ]),
            use_container_width=True,
            height=420
        )

    # ---------- Comparaison DEUX PÉRIODES ----------
    else:
        st.markdown("#### 🕑 Comparaison de deux périodes")

        colp1, colp2 = st.columns(2)

        with colp1:
            st.subheader("Période 1")
            date1_start = st.date_input("Date début 1", value=df["_Date_"].min().date())
            date1_end = st.date_input("Date fin 1", value=df["_Date_"].max().date())
        with colp2:
            st.subheader("Période 2")
            date2_start = st.date_input("Date début 2", value=df["_Date_"].min().date(), key="d2start")
            date2_end = st.date_input("Date fin 2", value=df["_Date_"].max().date(), key="d2end")

        # Filtrage des deux périodes
        df_period1 = df_f[(df_f["_Date_"] >= pd.to_datetime(date1_start)) & (df_f["_Date_"] <= pd.to_datetime(date1_end))]
        df_period2 = df_f[(df_f["_Date_"] >= pd.to_datetime(date2_start)) & (df_f["_Date_"] <= pd.to_datetime(date2_end))]

        def aggr_period(df_):
            return {
                "Nombre de dossiers": len(df_),
                "Montant facturé": df_["Montant facturé"].sum(),
                "Montant honoraires (US $)": df_[col_mh].sum(),
                "Autres frais (US $)": df_[col_autre].sum()
            }
        aggr1 = aggr_period(df_period1)
        aggr2 = aggr_period(df_period2)

        comp_df = pd.DataFrame({
            "Période 1": [aggr1["Nombre de dossiers"], aggr1["Montant facturé"], aggr1["Montant honoraires (US $)"], aggr1["Autres frais (US $)"]],
            "Période 2": [aggr2["Nombre de dossiers"], aggr2["Montant facturé"], aggr2["Montant honoraires (US $)"], aggr2["Autres frais (US $)"]],
        }, index=["Nombre de dossiers", "Montant facturé", "Montant honoraires (US $)", "Autres frais (US $)"])

        # Formatage des montants ($)
        for col in comp_df.columns:
            comp_df.loc["Montant facturé", col] = _fmt_money(comp_df.loc["Montant facturé", col])
            comp_df.loc["Montant honoraires (US $)", col] = _fmt_money(comp_df.loc["Montant honoraires (US $)", col])
            comp_df.loc["Autres frais (US $)", col] = _fmt_money(comp_df.loc["Autres frais (US $)", col])

        st.markdown("##### 🔎 Comparatif de périodes")
        st.dataframe(comp_df, use_container_width=True, height=220)

        # Liste dossiers des périodes
        st.markdown("#### 🧾 Dossiers de la période 1")
        if not df_period1.empty:
            st.dataframe(df_period1[["Nom", col_mh, col_autre, "Montant facturé", "_Date_"]], use_container_width=True)
        else:
            st.info("Aucun dossier sur cette période.")
        st.markdown("#### 🧾 Dossiers de la période 2")
        if not df_period2.empty:
            st.dataframe(df_period2[["Nom", col_mh, col_autre, "Montant facturé", "_Date_"]], use_container_width=True)
        else:
            st.info("Aucun dossier sur cette période.")
