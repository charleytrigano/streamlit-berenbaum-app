# app.py — Version stable multi-feuilles
# Lecture forcée de la feuille "Clients" pour le Dashboard

import streamlit as st
import pandas as pd
from pathlib import Path

# === PARAMÈTRES GLOBAUX ======================================================
DEFAULT_XLSX = "Clients BL.xlsx"
st.set_page_config(page_title="Visa Manager", layout="wide")

# === 1. CHARGEMENT COMPLET DU FICHIER EXCEL =================================
@st.cache_data(show_spinner=False)
def _read_all_sheets():
    """Lit toutes les feuilles du fichier Excel et les retourne sous forme de dict."""
    xls_path = Path(DEFAULT_XLSX)
    if not xls_path.exists():
        st.warning(f"⚠️ Fichier « {DEFAULT_XLSX} » introuvable à la racine du projet.")
        return {}

    try:
        xls = pd.ExcelFile(xls_path)
        data = {}
        for sheet in xls.sheet_names:
            try:
                df = pd.read_excel(xls, sheet)
                data[sheet] = df
            except Exception as e:
                st.warning(f"Erreur lecture feuille « {sheet} » : {e}")
        return data
    except Exception as e:
        st.error(f"Erreur lecture « {DEFAULT_XLSX} » : {e}")
        return {}

if "data_xlsx" not in st.session_state:
    st.session_state["data_xlsx"] = _read_all_sheets()


# === 2. OUTILS NUMÉRIQUES ====================================================
def _clean_number_series(s: pd.Series) -> pd.Series:
    """Nettoie les séries de montants (texte → float)."""
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

def _ensure_cols(df: pd.DataFrame, cols):
    for c in cols:
        if c not in df.columns:
            df[c] = 0.0
    return df


# === 3. ONGLET FICHIERS ======================================================
def tab_fichiers():
    st.header("📄 Fichiers")

    data = st.session_state.get("data_xlsx", {})
    if data:
        st.success(f"📚 {len(data)} feuille(s) chargée(s) : {', '.join(data.keys())}")
        sheet = st.selectbox("Afficher une feuille :", list(data.keys()))
        st.dataframe(data[sheet].head(20), use_container_width=True, hide_index=True)
    else:
        st.warning("Aucune donnée chargée. Place ton fichier Excel à la racine du projet.")

    st.markdown("---")
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("🔄 Recharger le fichier par défaut")
        if st.button(f"Recharger « {DEFAULT_XLSX} »"):
            st.session_state["data_xlsx"] = _read_all_sheets()
            st.success("✅ Données rechargées.")
            st.rerun()

    with c2:
        st.subheader("⬆️ Importer un autre fichier Excel")
        up = st.file_uploader("Choisir un .xlsx", type=["xlsx"])
        if up is not None:
            try:
                xls = pd.ExcelFile(up)
                data = {s: pd.read_excel(xls, s) for s in xls.sheet_names}
                st.session_state["data_xlsx"] = data
                st.success(f"{len(data)} feuille(s) importée(s).")
                st.rerun()
            except Exception as e:
                st.error(f"Erreur import : {e}")


# === 4. ONGLET DASHBOARD =====================================================
def tab_dashboard():
    st.header("📊 Tableau de bord")

    data = st.session_state.get("data_xlsx", {})
    if not data:
        st.warning("Aucune donnée Excel disponible.")
        return

    # 🔍 Lecture forcée de la feuille 'Clients'
    if "Clients" in data:
        df = data["Clients"].copy()
    else:
        st.error("Feuille 'Clients' introuvable dans le fichier Excel.")
        st.stop()

    if df.empty:
        st.warning("La feuille 'Clients' est vide ou mal formatée.")
        return

    # Colonnes importantes
    COL_HONO = "Montant honoraires (US $)"
    COL_AUTRES = "Autres frais (US $)"
    AC_COLS = ["Acompte 1", "Acompte 2", "Acompte 3", "Acompte 4"]

    # Nettoyage et calculs
    df = _ensure_cols(df, [COL_HONO, COL_AUTRES] + AC_COLS)
    df[COL_HONO] = _clean_number_series(df[COL_HONO])
    df[COL_AUTRES] = _clean_number_series(df[COL_AUTRES])
    for c in AC_COLS:
        df[c] = _clean_number_series(df[c])

    df["Montant facturé"] = df[COL_HONO] + df[COL_AUTRES]
    df["Total payé"] = df[AC_COLS].sum(axis=1)
    df["Solde restant"] = df["Montant facturé"] - df["Total payé"]

    # === Synthèse compacte
    st.markdown("### 📈 Synthèse financière")
    k1, k2, k3, k4, k5, k6 = st.columns(6)
    k1.metric("👥 Clients", f"{len(df)}")
    k2.metric("💼 Honoraires", f"{df[COL_HONO].sum():,.0f} US$")
    k3.metric("🧾 Autres frais", f"{df[COL_AUTRES].sum():,.0f} US$")
    k4.metric("💰 Facturé", f"{df['Montant facturé'].sum():,.0f} US$")
    k5.metric("💸 Payé", f"{df['Total payé'].sum():,.0f} US$")
    k6.metric("📉 Solde", f"{df['Solde restant'].sum():,.0f} US$")

    # === Dossiers
    st.markdown("---")
    st.subheader("📋 Dossiers clients")
    show_cols = [c for c in df.columns if c in ["Nom", COL_HONO, COL_AUTRES, "Montant facturé", "Total payé", "Solde restant"]]
    if not show_cols:
        show_cols = df.columns.tolist()[:6]
    st.dataframe(df[show_cols], use_container_width=True, hide_index=True)

    # === Top 10 (tableau, pas graphique)
    st.markdown("---")
    st.subheader("🏆 Top 10 par montant facturé")
    top10 = df.sort_values("Montant facturé", ascending=False).head(10)
    st.dataframe(top10[show_cols], use_container_width=True, hide_index=True)


# === 5. ONGLET ESCROW ========================================================
def tab_escrow():
    st.header("🛡️ Escrow")

    data = st.session_state.get("data_xlsx", {})
    if not data or "Escrow" not in data:
        st.warning("Feuille 'Escrow' introuvable dans le fichier Excel.")
        return

    df = data["Escrow"].copy()
    st.dataframe(df, use_container_width=True, hide_index=True)


# === 6. ONGLET COMPTA CLIENT ================================================
def tab_compta():
    st.header("💳 Compta Client")

    data = st.session_state.get("data_xlsx", {})
    if not data or "ComptaCli" not in data:
        st.warning("Feuille 'ComptaCli' non trouvée.")
        return

    df = data["ComptaCli"].copy()
    st.dataframe(df, use_container_width=True, hide_index=True)


# === 7. ONGLET VISA =========================================================
def tab_visa():
    st.header("🛂 Visa")

    data = st.session_state.get("data_xlsx", {})
    if not data or "Visa" not in data:
        st.warning("Feuille 'Visa' non trouvée.")
        return

    df = data["Visa"].copy()
    st.dataframe(df, use_container_width=True, hide_index=True)


# === 8. BARRE DE NAVIGATION =================================================
tabs = st.tabs([
    "📄 Fichiers",
    "📊 Tableau de bord",
    "🛂 Visa",
    "💳 Compta Client",
    "🛡️ Escrow"
])

with tabs[0]:
    tab_fichiers()
with tabs[1]:
    tab_dashboard()
with tabs[2]:
    tab_visa()
with tabs[3]:
    tab_compta()
with tabs[4]:
    tab_escrow()