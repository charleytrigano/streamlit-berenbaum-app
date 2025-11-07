# app.py — version intégrale fonctionnelle

import streamlit as st
import pandas as pd
from pathlib import Path


# === 1. Chargement automatique du fichier Excel ==============================
DEFAULT_XLSX = "Clients BL.xlsx"

@st.cache_data(show_spinner=False)
def _read_default_excel():
    xls_path = Path(DEFAULT_XLSX)
    if xls_path.exists():
        try:
            xls = pd.ExcelFile(xls_path)
            sheet = "Clients" if "Clients" in xls.sheet_names else xls.sheet_names[0]
            df = pd.read_excel(xls, sheet)
            return df
        except Exception as e:
            st.error(f"Erreur lecture '{DEFAULT_XLSX}': {e}")
    return pd.DataFrame()

if "clients_df" not in st.session_state:
    st.session_state["clients_df"] = _read_default_excel()


# === 2. Onglet Fichiers ======================================================
def tab_fichiers():
    st.header("📄 Fichiers")

    cur = st.session_state.get("clients_df")
    if cur is not None and not cur.empty:
        st.success(f"📦 Données chargées ({len(cur)} lignes).")
        st.dataframe(cur.head(20), use_container_width=True, hide_index=True)
    else:
        st.warning("Aucune donnée en mémoire.")

    st.markdown("---")

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🔄 Recharger le fichier par défaut")
        if st.button(f"Recharger « {DEFAULT_XLSX} »"):
            df = _read_default_excel()
            if df.empty:
                st.error(f"Impossible de charger « {DEFAULT_XLSX} ». Place le fichier à la racine du projet.")
            else:
                st.session_state["clients_df"] = df
                st.success("Fichier par défaut rechargé.")
                st.experimental_rerun()

    with c2:
        st.subheader("⬆️ Importer un autre Excel")
        up = st.file_uploader("Choisir un .xlsx", type=["xlsx"])
        if up is not None:
            try:
                xls = pd.ExcelFile(up)
                sheet = "Clients" if "Clients" in xls.sheet_names else xls.sheet_names[0]
                df = pd.read_excel(xls, sheet)
            except Exception as e:
                st.error(f"Erreur lecture Excel : {e}")
                df = pd.DataFrame()

            if df.empty:
                st.error("Le fichier importé est vide ou illisible.")
            else:
                st.session_state["clients_df"] = df
                st.success("Nouvelles données chargées.")
                st.experimental_rerun()


# === 3. Utilitaires de nettoyage =============================================
def _clean_number_series(s: pd.Series) -> pd.Series:
    if s is None:
        return pd.Series(dtype=float)
    s = s.astype(str)
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
    return pd.to_numeric(s, errors="coerce").fillna(0.0)

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


# === 4. Onglet Tableau de bord ===============================================
def tab_dashboard():
    st.header("📊 Tableau de bord")

    df_src = st.session_state.get("clients_df")

    # Fallback automatique si vide
    if df_src is None or df_src.empty:
        df_src = _read_default_excel()
        st.session_state["clients_df"] = df_src

    if df_src is None or df_src.empty:
        st.warning("Aucune donnée disponible. Chargez un fichier dans l’onglet 📄 Fichiers.")
        return

    COL_HONO = "Montant honoraires (US $)"
    COL_AUTRES = "Autres frais (US $)"
    AC_COLS = ["Acompte 1", "Acompte 2", "Acompte 3", "Acompte 4"]

    COL_NOM = _first_existing(df_src, ["Nom", "Client", "Client Name"])
    COL_CAT = _first_existing(df_src, ["Catégorie", "Categorie", "Category"])
    COL_SUB = _first_existing(df_src, ["Sous-catégorie", "Sous categorie", "Sous catégorie", "Subcategory"])
    COL_VISA = _first_existing(df_src, ["Type de visa", "Visa", "Type Visa"])
    COL_DATE = _first_existing(df_src, ["Date dossier", "Date", "Date envoi", "Date Dossier"])

    df = df_src.copy()
    df = _ensure_cols(df, [COL_HONO, COL_AUTRES] + AC_COLS)
    df[COL_HONO] = _clean_number_series(df[COL_HONO])
    df[COL_AUTRES] = _clean_number_series(df[COL_AUTRES])
    for c in AC_COLS:
        df[c] = _clean_number_series(df[c])

    if COL_DATE:
        df[COL_DATE] = pd.to_datetime(df[COL_DATE], errors="coerce")
        df["__Année__"] = df[COL_DATE].dt.year
        mois_labels = {
            1:"Janvier",2:"Février",3:"Mars",4:"Avril",5:"Mai",6:"Juin",
            7:"Juillet",8:"Août",9:"Septembre",10:"Octobre",11:"Novembre",12:"Décembre"
        }
        df["__Mois__"] = df[COL_DATE].dt.month.map(mois_labels)
    else:
        df["__Année__"] = pd.NA
        df["__Mois__"] = pd.NA

    df["Montant facturé"] = df[COL_HONO] + df[COL_AUTRES]
    df["Total payé"] = df[AC_COLS].sum(axis=1)
    df["Solde restant"] = df["Montant facturé"] - df["Total payé"]

    # ---------- Filtres ----------
    st.markdown("### 🔍 Filtres")
    cols_filters = st.columns(5)

    opts_cat = sorted(df[COL_CAT].dropna().unique()) if COL_CAT else []
    opts_sub = sorted(df[COL_SUB].dropna().unique()) if COL_SUB else []
    opts_visa = sorted(df[COL_VISA].dropna().unique()) if COL_VISA else []
    opts_year = sorted(df["__Année__"].dropna().unique()) if "__Année__" in df else []
    opts_month = [m for m in [
        "Janvier","Février","Mars","Avril","Mai","Juin","Juillet","Août",
        "Septembre","Octobre","Novembre","Décembre"
    ] if "__Mois__" in df and m in set(df["__Mois__"].dropna().unique())]

    sel_cat = cols_filters[0].multiselect("Catégorie", opts_cat)
    sel_sub = cols_filters[1].multiselect("Sous-catégorie", opts_sub)
    sel_visa = cols_filters[2].multiselect("Visa", opts_visa)
    sel_year = cols_filters[3].multiselect("Année", opts_year)
    sel_month = cols_filters[4].multiselect("Mois", opts_month)

    filt = pd.Series(True, index=df.index)
    if sel_cat and COL_CAT: filt &= df[COL_CAT].isin(sel_cat)
    if sel_sub and COL_SUB: filt &= df[COL_SUB].isin(sel_sub)
    if sel_visa and COL_VISA: filt &= df[COL_VISA].isin(sel_visa)
    if sel_year: filt &= df["__Année__"].isin(sel_year)
    if sel_month: filt &= df["__Mois__"].isin(sel_month)
    df_f = df[filt].copy()

    # ---------- KPI (petits) ----------
    st.markdown("""
        <style>
        div[data-testid="stMetricValue"] {font-size:0.85rem !important;}
        div[data-testid="stMetricLabel"] {font-size:0.70rem !important;}
        </style>
    """, unsafe_allow_html=True)

    st.markdown("### 📈 Synthèse financière")
    k1,k2,k3,k4,k5,k6 = st.columns(6)
    k1.metric("👥 Clients", f"{len(df_f)}")
    k2.metric("💼 Honoraires", f"{df_f[COL_HONO].sum():,.2f} US$")
    k3.metric("🧾 Autres frais", f"{df_f[COL_AUTRES].sum():,.2f} US$")
    k4.metric("💰 Montant facturé", f"{df_f['Montant facturé'].sum():,.2f} US$")
    k5.metric("💸 Total payé", f"{df_f['Total payé'].sum():,.2f} US$")
    k6.metric("🧾 Solde restant", f"{df_f['Solde restant'].sum():,.2f} US$")

    # ---------- Tableau principal ----------
    st.markdown("---")
    st.subheader("📋 Dossiers filtrés")
    show_cols = [c for c in [COL_NOM, COL_HONO, COL_AUTRES, "Montant facturé", "Total payé", "Solde restant"] if c]
    st.dataframe(df_f[show_cols], use_container_width=True, hide_index=True)

    # ---------- Comparatif ----------
    if "__Année__" in df and df["__Année__"].notna().any():
        st.markdown("---")
        st.subheader("📆 Comparatif entre périodes")
        colA, colB = st.columns(2)
        years = sorted(df["__Année__"].dropna().unique())
        year_a = colA.selectbox("Période A", years, index=0)
        year_b = colB.selectbox("Période B", years, index=min(1, len(years)-1))

        A = df_f[df_f["__Année__"] == year_a]
        B = df_f[df_f["__Année__"] == year_b]

        def stats(x):
            return pd.Series({
                "Clients": len(x),
                "Facturé": x["Montant facturé"].sum(),
                "Payé": x["Total payé"].sum(),
                "Solde": x["Solde restant"].sum(),
            })

        tA, tB = stats(A), stats(B)
        comp = pd.DataFrame({
            "Indicateur": tA.index,
            f"{int(year_a)}": tA.values,
            f"{int(year_b)}": tB.values,
            "Δ (B-A)": (tB - tA).values,
        })
        st.dataframe(comp, use_container_width=True, hide_index=True)

    # ---------- Top 10 ----------
    st.markdown("---")
    st.subheader("🏆 Top 10 par montant facturé")
    top10 = df_f.sort_values("Montant facturé", ascending=False)
    top10 = top10[[COL_NOM, "Montant facturé", "Total payé", "Solde restant"]].head(10) if COL_NOM else \
            top10[["Montant facturé", "Total payé", "Solde restant"]].head(10)
    st.dataframe(top10, use_container_width=True, hide_index=True)


# === 5. Application principale ===============================================
st.set_page_config(page_title="Visa Manager", layout="wide")
tabs = st.tabs(["📄 Fichiers", "📊 Tableau de bord"])

with tabs[0]:
    tab_fichiers()
with tabs[1]:
    tab_dashboard()
