import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="📊 Visa Dashboard", layout="wide")

# === CONFIGURATION ===
EXCEL_FILE = "Clients BL.xlsx"
SHEET_NAME = "Clients"

# === FONCTIONS ===
@st.cache_data
def load_excel(path: str):
    if not os.path.exists(path):
        st.error(f"❌ Fichier introuvable : {path}")
        return None
    try:
        xls = pd.ExcelFile(path)
        if SHEET_NAME not in xls.sheet_names:
            st.error(f"❌ Feuille '{SHEET_NAME}' introuvable dans le fichier.")
            return None
        df = pd.read_excel(xls, SHEET_NAME)
        return df
    except Exception as e:
        st.error(f"Erreur lors du chargement du fichier : {e}")
        return None

def clean_numeric(df, cols):
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
    return df

# === CHARGEMENT AUTOMATIQUE ===
df = load_excel(EXCEL_FILE)

if df is None or df.empty:
    st.warning("⚠️ Impossible de charger le fichier Excel. Vérifie le nom ou la feuille.")
    st.stop()

# === NORMALISATION ===
df.columns = [c.strip() for c in df.columns]
df = clean_numeric(df, [
    "Montant honoraires (US $)",
    "Autres frais (US $)",
    "Acompte 1",
    "Acompte 2",
    "Acompte 3",
    "Acompte 4"
])

# === CALCULS FINANCIERS ===
df["Montant facturé"] = df["Montant honoraires (US $)"] + df["Autres frais (US $)"]
df["Total payé"] = df[["Acompte 1", "Acompte 2", "Acompte 3", "Acompte 4"]].sum(axis=1)
df["Solde restant"] = df["Montant facturé"] - df["Total payé"]

# === FILTRES ===
with st.expander("🔍 Filtres"):
    cols = st.columns(5)
    f_cat = cols[0].selectbox("Catégorie", ["(Toutes)"] + sorted(df["Catégorie"].dropna().unique().tolist())) if "Catégorie" in df.columns else "(Toutes)"
    f_scat = cols[1].selectbox("Sous-catégorie", ["(Toutes)"] + sorted(df["Sous-catégorie"].dropna().unique().tolist())) if "Sous-catégorie" in df.columns else "(Toutes)"
    f_visa = cols[2].selectbox("Visa", ["(Tous)"] + sorted(df["Visa"].dropna().unique().tolist())) if "Visa" in df.columns else "(Tous)"
    f_annee = cols[3].selectbox("Année", ["(Toutes)"] + sorted(df["Année"].dropna().unique().tolist())) if "Année" in df.columns else "(Toutes)"
    f_mois = cols[4].selectbox("Mois", ["(Tous)"] + sorted(df["Mois"].dropna().unique().tolist())) if "Mois" in df.columns else "(Tous)"

# Application des filtres
mask = pd.Series(True, index=df.index)
if f_cat != "(Toutes)": mask &= df["Catégorie"] == f_cat
if f_scat != "(Toutes)": mask &= df["Sous-catégorie"] == f_scat
if f_visa != "(Tous)": mask &= df["Visa"] == f_visa
if f_annee != "(Toutes)": mask &= df["Année"] == f_annee
if f_mois != "(Tous)": mask &= df["Mois"] == f_mois
df_filtered = df[mask]

# === KPIs COMPACTS ===
st.markdown("## 📈 Synthèse financière")
c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("👥 Clients", f"{len(df_filtered)}")
c2.metric("💼 Honoraires", f"{df_filtered['Montant honoraires (US $)'].sum():,.0f} US$")
c3.metric("🧾 Autres frais", f"{df_filtered['Autres frais (US $)'].sum():,.0f} US$")
c4.metric("💰 Facturé", f"{df_filtered['Montant facturé'].sum():,.0f} US$")
c5.metric("💸 Payé", f"{df_filtered['Total payé'].sum():,.0f} US$")
c6.metric("📉 Solde", f"{df_filtered['Solde restant'].sum():,.0f} US$")

# === TABLEAU COMPLET ===
st.markdown("---")
st.subheader("📋 Dossiers clients filtrés")
cols_show = ["Nom", "Montant honoraires (US $)", "Autres frais (US $)", "Montant facturé", "Total payé", "Solde restant"]
cols_show = [c for c in cols_show if c in df_filtered.columns]
st.dataframe(df_filtered[cols_show], use_container_width=True, hide_index=True)

# === TOP 10 PAR MONTANT FACTURÉ ===
st.markdown("---")
st.subheader("🏆 Top 10 par montant facturé")
top10 = df_filtered.sort_values("Montant facturé", ascending=False).head(10)
st.dataframe(top10[cols_show], use_container_width=True, hide_index=True)
