import streamlit as st
import pandas as pd

# ---------- Utils ----------
def _clean_number_series(s: pd.Series) -> pd.Series:
    if s is None:
        return pd.Series(dtype=float)
    s = s.astype(str)
    neg_mask = s.str.contains(r"^\s*\(.*\)\s*$")

    s = (
        s.str.replace("\u202f", "", regex=False)
         .str.replace("\xa0", "", regex=False)
         .str.replace(" ", "", regex=False)
         .str.replace(r"[^\d\-,\.]", "", regex=True)
    )
    both = s.str.contains(r"\.") & s.str.contains(r",")
    s = s.where(~both, s.str.replace(",", "", regex=False))
    only_comma = s.str.contains(r",") & ~both
    s = s.where(~only_comma, s.str.replace(",", ".", regex=False))
    s = s.replace("", "0")
    out = pd.to_numeric(s, errors="coerce").fillna(0.0)
    out = out.where(~neg_mask, -out)
    return out

def _ensure_cols(df: pd.DataFrame, cols) -> pd.DataFrame:
    for c in cols:
        if c not in df.columns:
            df[c] = 0.0
    return df

def _first_existing(df: pd.DataFrame, candidates):
    for c in candidates:
        if c in df.columns:
            return c
    return None

# ---------- Main ----------
def main():
    st.header("📊 Tableau de bord")

    df_src = st.session_state.get("clients_df")
    if df_src is None or df_src.empty:
        st.warning("Aucune donnée disponible. Chargez un fichier dans l’onglet 📄 Fichiers.")
        return

    # Colonnes clés chiffrées
    COL_HONO   = "Montant honoraires (US $)"
    COL_AUTRES = "Autres frais (US $)"
    AC_COLS    = ["Acompte 1", "Acompte 2", "Acompte 3", "Acompte 4"]

    # Colonnes d’info/filtre (on détecte au mieux)
    COL_NOM   = _first_existing(df_src, ["Nom", "Client", "Client Name"])
    COL_CAT   = _first_existing(df_src, ["Catégorie", "Categorie", "Category"])
    COL_SUB   = _first_existing(df_src, ["Sous-catégorie", "Sous categorie", "Sous catégorie", "Subcategory"])
    COL_VISA  = _first_existing(df_src, ["Type de visa", "Visa", "Type Visa"])
    COL_DATE  = _first_existing(df_src, ["Date dossier", "Date", "Date envoi", "Date Dossier"])

    df = df_src.copy()

    # Sécuriser colonnes numériques
    df = _ensure_cols(df, [COL_HONO, COL_AUTRES] + AC_COLS)

    # Nettoyage valeurs numériques
    df[COL_HONO]   = _clean_number_series(df[COL_HONO])
    df[COL_AUTRES] = _clean_number_series(df[COL_AUTRES])
    for c in AC_COLS:
        df[c] = _clean_number_series(df[c])

    # Date → Année / Mois si dispo
    if COL_DATE:
        df[COL_DATE] = pd.to_datetime(df[COL_DATE], errors="coerce")
        df["__Année__"] = df[COL_DATE].dt.year
        # Mois texte FR : fallback si locale indisponible
        df["__Mois__"] = df[COL_DATE].dt.month
        mois_labels = {
            1:"Janvier",2:"Février",3:"Mars",4:"Avril",5:"Mai",6:"Juin",
            7:"Juillet",8:"Août",9:"Septembre",10:"Octobre",11:"Novembre",12:"Décembre"
        }
        df["__Mois__"] = df["__Mois__"].map(mois_labels)
    else:
        df["__Année__"] = pd.NA
        df["__Mois__"]  = pd.NA

    # Calculs de base
    df["Montant facturé"] = df[COL_HONO] + df[COL_AUTRES]
    df["Total payé"]      = df[AC_COLS].sum(axis=1)
    df["Solde restant"]   = df["Montant facturé"] - df["Total payé"]

    # ---------- Filtres ----------
    st.markdown("### 🔍 Filtres")

    cols_filters = st.columns(5)
    # On ne montre un filtre que si la colonne existe, sinon multiselect vide (désactivé)
    opts_cat   = sorted(df[COL_CAT].dropna().unique()) if COL_CAT and df[COL_CAT].notna().any() else []
    opts_sub   = sorted(df[COL_SUB].dropna().unique()) if COL_SUB and df[COL_SUB].notna().any() else []
    opts_visa  = sorted(df[COL_VISA].dropna().unique()) if COL_VISA and df[COL_VISA].notna().any() else []
    opts_year  = sorted(df["__Année__"].dropna().unique()) if df["__Année__"].notna().any() else []
    opts_month = [m for m in ["Janvier","Février","Mars","Avril","Mai","Juin","Juillet","Août","Septembre","Octobre","Novembre","Décembre"]
                  if m in set(df["__Mois__"].dropna().unique())]

    sel_cat   = cols_filters[0].multiselect("Catégorie", opts_cat, default=[])
    sel_sub   = cols_filters[1].multiselect("Sous-catégorie", opts_sub, default=[])
    sel_visa  = cols_filters[2].multiselect("Visa", opts_visa, default=[])
    sel_year  = cols_filters[3].multiselect("Année", opts_year, default=[])
    sel_month = cols_filters[4].multiselect("Mois", opts_month, default=[])

    filt = pd.Series(True, index=df.index)
    if sel_cat   and COL_CAT:  filt &= df[COL_CAT].isin(sel_cat)
    if sel_sub   and COL_SUB:  filt &= df[COL_SUB].isin(sel_sub)
    if sel_visa  and COL_VISA: filt &= df[COL_VISA].isin(sel_visa)
    if sel_year:               filt &= df["__Année__"].isin(sel_year)
    if sel_month:              filt &= df["__Mois__"].isin(sel_month)

    df_f = df[filt].copy()

    # ---------- KPI petits / une ligne ----------
    st.markdown("""
        <style>
        div[data-testid="stMetricValue"] {font-size:0.85rem !important;}
        div[data-testid="stMetricLabel"] {font-size:0.70rem !important;}
        section.main > div {padding-top: 0.5rem;}
        </style>
    """, unsafe_allow_html=True)

    st.markdown("### 📈 Synthèse financière")
    k1,k2,k3,k4,k5,k6 = st.columns(6)
    total_clients = int(len(df_f))
    total_hono    = float(df_f[COL_HONO].sum())
    total_autres  = float(df_f[COL_AUTRES].sum())
    total_fact    = float(df_f["Montant facturé"].sum())
    total_paye    = float(df_f["Total payé"].sum())
    total_solde   = float(df_f["Solde restant"].sum())

    k1.metric("👥 Clients", f"{total_clients}")
    k2.metric("💼 Honoraires", f"{total_hono:,.2f} US$")
    k3.metric("🧾 Autres frais", f"{total_autres:,.2f} US$")
    k4.metric("💰 Montant facturé", f"{total_fact:,.2f} US$")
    k5.metric("💸 Total payé", f"{total_paye:,.2f} US$")
    k6.metric("🧾 Solde restant", f"{total_solde:,.2f} US$")

    st.markdown("---")

    # ---------- Tableau des dossiers (filtrés) ----------
    st.subheader("📋 Dossiers (après filtres)")
    cols_show = [c for c in [COL_NOM, COL_HONO, COL_AUTRES, "Montant facturé", "Total payé", "Solde restant"] if c]
    if not cols_show:
        cols_show = ["Montant facturé", "Total payé", "Solde restant"]
    st.dataframe(df_f[cols_show], use_container_width=True, hide_index=True)

    # ---------- Comparatif de périodes ----------
    st.markdown("---")
    st.subheader("📆 Comparatif entre périodes (tableau)")

    if df["__Année__"].notna().any():
        colA, colB = st.columns(2)
        years = sorted(df["__Année__"].dropna().unique())
        year_a = colA.selectbox("Période A (Année)", years, index=0, key="cmpA")
        year_b = colB.selectbox("Période B (Année)", years, index=min(1, len(years)-1), key="cmpB")

        A = df_f[df_f["__Année__"] == year_a]
        B = df_f[df_f["__Année__"] == year_b]

        def stats(x):
            return pd.Series({
                "Clients": len(x),
                "Honoraires (US$)": x[COL_HONO].sum(),
                "Autres frais (US$)": x[COL_AUTRES].sum(),
                "Montant facturé (US$)": x["Montant facturé"].sum(),
                "Total payé (US$)": x["Total payé"].sum(),
                "Solde restant (US$)": x["Solde restant"].sum(),
            })

        tA = stats(A)
        tB = stats(B)
        comp = pd.DataFrame({
            "Indicateur": tA.index,
            f"{int(year_a)}": tA.values,
            f"{int(year_b)}": tB.values,
            "Δ (B - A)": (tB - tA).values,
            "Δ %": ((tB - tA) / tA.replace(0, pd.NA) * 100).astype(float).round(2).astype(str).replace("<NA>", "—")
        })
        st.dataframe(comp, use_container_width=True, hide_index=True)
    else:
        st.info("Pas de colonne de date détectée : comparatif par période indisponible.")

    # ---------- Top 10 en tableau (et comparatif) ----------
    st.markdown("---")
    st.subheader("🏆 Top 10 par Montant facturé (table)")

    top10 = df_f.sort_values("Montant facturé", ascending=False)
    top10 = top10[[COL_NOM, "Montant facturé", "Total payé", "Solde restant"]].head(10) if COL_NOM else \
            top10[["Montant facturé", "Total payé", "Solde restant"]].head(10)
    st.dataframe(top10, use_container_width=True, hide_index=True)

    # Comparatif Top 10 A vs B (si années)
    if df["__Année__"].notna().any():
        st.markdown("#### 🔀 Comparatif Top 10 — Période A vs Période B")
        A10 = df_f[df_f["__Année__"] == year_a].sort_values("Montant facturé", ascending=False)
        B10 = df_f[df_f["__Année__"] == year_b].sort_values("Montant facturé", ascending=False)

        A10 = A10[[COL_NOM, "Montant facturé", "Total payé", "Solde restant"]].head(10) if COL_NOM else \
              A10[["Montant facturé", "Total payé", "Solde restant"]].head(10)
        B10 = B10[[COL_NOM, "Montant facturé", "Total payé", "Solde restant"]].head(10) if COL_NOM else \
              B10[["Montant facturé", "Total payé", "Solde restant"]].head(10)

        colL, colR = st.columns(2)
        with colL:
            st.markdown(f"**Top 10 — {int(year_a)}**")
            st.dataframe(A10, use_container_width=True, hide_index=True)
        with colR:
            st.markdown(f"**Top 10 — {int(year_b)}**")
            st.dataframe(B10, use_container_width=True, hide_index=True)
