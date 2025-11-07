import streamlit as st
import pandas as pd
import re

# === Nettoyage des montants ===
def _clean_number_series(s: pd.Series) -> pd.Series:
    """Nettoie et convertit une série de valeurs monétaires en float."""
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

# === Sécurisation colonnes ===
def _ensure_cols(df: pd.DataFrame, cols) -> pd.DataFrame:
    for c in cols:
        if c not in df.columns:
            df[c] = 0.0
    return df

# === Tableau de bord ===
def main():
    st.header("📊 Tableau de bord")

    df_src = st.session_state.get("clients_df")
    if df_src is None or df_src.empty:
        st.warning("Aucune donnée disponible. Chargez un fichier dans l’onglet 📄 Fichiers.")
        return

    COL_HONO = "Montant honoraires (US $)"
    COL_AUTRES = "Autres frais (US $)"
    AC_COLS = ["Acompte 1", "Acompte 2", "Acompte 3", "Acompte 4"]

    df = df_src.copy()
    needed = [COL_HONO, COL_AUTRES] + AC_COLS
    df = _ensure_cols(df, needed)

    # Nettoyage
    df[COL_HONO] = _clean_number_series(df[COL_HONO])
    df[COL_AUTRES] = _clean_number_series(df[COL_AUTRES])
    for c in AC_COLS:
        df[c] = _clean_number_series(df[c])

    # Calculs
    df["Montant facturé"] = df[COL_HONO] + df[COL_AUTRES]
    df["Total payé"] = df[AC_COLS].sum(axis=1)
    df["Solde restant"] = df["Montant facturé"] - df["Total payé"]

    total_clients = len(df)
    total_hono = df[COL_HONO].sum()
    total_autres = df[COL_AUTRES].sum()
    total_facture = df["Montant facturé"].sum()
    total_paye = df["Total payé"].sum()
    solde_restant = df["Solde restant"].sum()
    pourcent_paye = total_paye / total_facture * 100 if total_facture > 0 else 0

    # --- Style KPI réduits ---
    st.markdown("""
        <style>
        div[data-testid="stMetricValue"] {font-size:0.9rem !important;}
        div[data-testid="stMetricLabel"] {font-size:0.75rem !important;}
        </style>
    """, unsafe_allow_html=True)

    # === Synthèse financière sur une seule ligne ===
    st.markdown("### 📈 Synthèse financière")
    c1, c2, c3, c4, c5, c6 = st.columns(6)

    c1.metric("👥 Clients", f"{total_clients}")
    c2.metric("💼 Honoraires", f"{total_hono:,.2f} US$")
    c3.metric("🧾 Autres frais", f"{total_autres:,.2f} US$")
    c4.metric("💰 Montant facturé", f"{total_facture:,.2f} US$")
    c5.metric("💸 Total payé", f"{total_paye:,.2f} US$")

    color = "green" if solde_restant == 0 else ("orange" if solde_restant < 0.2 * total_facture else "red")
    solde_html = f"<span style='color:{color};font-weight:bold'>{solde_restant:,.2f} US$</span>"
    c6.markdown(f"<div style='font-size:0.9rem;'>🧾 Solde restant<br>{solde_html}</div>", unsafe_allow_html=True)

    st.markdown("---")

    # === Tableau complet avec coloration dynamique ===
    st.subheader("📋 Liste complète des dossiers")
    df_display = df[["Nom", COL_HONO, COL_AUTRES, "Montant facturé", "Total payé", "Solde restant"]].copy()
    def _row_color(x):
        if x["Solde restant"] == 0:
            return ['background-color: #b6f2b6'] * len(x)
        elif x["Solde restant"] < 0.2 * x["Montant facturé"]:
            return ['background-color: #fff4b3'] * len(x)
        else:
            return ['background-color: #fcb6b6'] * len(x)
    st.dataframe(
        df_display.style.apply(_row_color, axis=1),
        use_container_width=True,
        hide_index=True
    )

    # === Graphique top 10 ===
    st.markdown("### 📊 Top 10 par montant facturé")
    top10 = df.nlargest(10, "Montant facturé")
    if "Nom" in top10.columns:
        st.bar_chart(top10.set_index("Nom")["Montant facturé"])
    else:
        st.bar_chart(top10["Montant facturé"])

import streamlit as st
import pandas as pd
import re

# === Nettoyage des montants ===
def _clean_number_series(s: pd.Series) -> pd.Series:
    """Nettoie et convertit une série de valeurs monétaires en float."""
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

# === Sécurisation colonnes ===
def _ensure_cols(df: pd.DataFrame, cols) -> pd.DataFrame:
    for c in cols:
        if c not in df.columns:
            df[c] = 0.0
    return df


# === Tableau de bord principal ===
def main():
    st.header("📊 Tableau de bord")

    df_src = st.session_state.get("clients_df")
    if df_src is None or df_src.empty:
        st.warning("Aucune donnée disponible. Chargez un fichier dans l’onglet 📄 Fichiers.")
        return

    # Colonnes clés
    COL_HONO = "Montant honoraires (US $)"
    COL_AUTRES = "Autres frais (US $)"
    AC_COLS = ["Acompte 1", "Acompte 2", "Acompte 3", "Acompte 4"]

    # Colonnes potentielles de filtre
    CAT_COL = "Catégorie"
    SUBCAT_COL = "Sous-catégorie"
    VISA_COL = "Type de visa"
    DATE_COL = "Date dossier"

    df = df_src.copy()
    df = _ensure_cols(df, [COL_HONO, COL_AUTRES] + AC_COLS)

    # Nettoyage et calculs
    df[COL_HONO] = _clean_number_series(df[COL_HONO])
    df[COL_AUTRES] = _clean_number_series(df[COL_AUTRES])
    for c in AC_COLS:
        df[c] = _clean_number_series(df[c])

    df["Montant facturé"] = df[COL_HONO] + df[COL_AUTRES]
    df["Total payé"] = df[AC_COLS].sum(axis=1)
    df["Solde restant"] = df["Montant facturé"] - df["Total payé"]

    # Conversion des dates si présentes
    if DATE_COL in df.columns:
        df["Date dossier"] = pd.to_datetime(df["Date dossier"], errors="coerce")
        df["Année"] = df["Date dossier"].dt.year
        df["Mois"] = df["Date dossier"].dt.month_name(locale="fr_FR")

    # === Filtres interactifs ===
    st.markdown("### 🔍 Filtres")
    f1, f2, f3, f4, f5 = st.columns(5)

    cat = f1.multiselect("Catégorie", sorted(df[CAT_COL].dropna().unique()) if CAT_COL in df.columns else [])
    subcat = f2.multiselect("Sous-catégorie", sorted(df[SUBCAT_COL].dropna().unique()) if SUBCAT_COL in df.columns else [])
    visa = f3.multiselect("Visa", sorted(df[VISA_COL].dropna().unique()) if VISA_COL in df.columns else [])
    annee = f4.multiselect("Année", sorted(df["Année"].dropna().unique()) if "Année" in df.columns else [])
    mois = f5.multiselect("Mois", sorted(df["Mois"].dropna().unique()) if "Mois" in df.columns else [])

    filt = pd.Series([True] * len(df))
    if cat: filt &= df[CAT_COL].isin(cat)
    if subcat: filt &= df[SUBCAT_COL].isin(subcat)
    if visa: filt &= df[VISA_COL].isin(visa)
    if annee: filt &= df["Année"].isin(annee)
    if mois: filt &= df["Mois"].isin(mois)
    df_filt = df[filt].copy()

    # === Sélection comparatif ===
    st.markdown("### 📆 Comparatif de périodes")
    colA, colB = st.columns(2)
    years = sorted(df["Année"].dropna().unique()) if "Année" in df.columns else []
    year_a = colA.selectbox("Période A (année)", years, key="comp_a")
    year_b = colB.selectbox("Période B (année)", years, key="comp_b")

    dfA = df[df["Année"] == year_a] if "Année" in df.columns else df.copy()
    dfB = df[df["Année"] == year_b] if "Année" in df.columns else df.copy()

    def calc_stats(df_):
        return {
            "Clients": len(df_),
            "Facturé": df_["Montant facturé"].sum(),
            "Payé": df_["Total payé"].sum(),
            "Solde": df_["Solde restant"].sum(),
        }

    statsA, statsB = calc_stats(dfA), calc_stats(dfB)

    delta_facture = statsB["Facturé"] - statsA["Facturé"]
    delta_paye = statsB["Payé"] - statsA["Payé"]

    # === Synthèse financière sur une seule ligne ===
    st.markdown("### 📈 Synthèse financière (filtres appliqués)")
    c1, c2, c3, c4, c5, c6 = st.columns(6)

    c1.metric("👥 Clients", len(df_filt))
    c2.metric("💼 Honoraires", f"{df_filt[COL_HONO].sum():,.2f} US$")
    c3.metric("🧾 Autres frais", f"{df_filt[COL_AUTRES].sum():,.2f} US$")
    c4.metric("💰 Montant facturé", f"{df_filt['Montant facturé'].sum():,.2f} US$")
    c5.metric("💸 Total payé", f"{df_filt['Total payé'].sum():,.2f} US$")
    c6.metric("💣 Solde restant", f"{df_filt['Solde restant'].sum():,.2f} US$")

    # === Comparatif ===
    st.markdown("---")
    st.subheader("📊 Comparatif entre périodes")
    st.write(f"**{year_a}** → Facturé : {statsA['Facturé']:,.2f} | Payé : {statsA['Payé']:,.2f}")
    st.write(f"**{year_b}** → Facturé : {statsB['Facturé']:,.2f} | Payé : {statsB['Payé']:,.2f}")
    st.write(f"🟢 Évolution du facturé : {delta_facture:+,.2f} US$")
    st.write(f"💵 Évolution du payé : {delta_paye:+,.2f} US$")

    # === Top 10 liste ===
    st.markdown("---")
    st.subheader("🏆 Top 10 par montant facturé")
    top10 = df_filt.nlargest(10, "Montant facturé")[["Nom", "Montant facturé", "Total payé", "Solde restant"]]
    for i, row in top10.iterrows():
        st.markdown(
            f"**{row['Nom']}** — Facturé: {row['Montant facturé']:,.2f} US$ | "
            f"Payé: {row['Total payé']:,.2f} US$ | Solde: {row['Solde restant']:,.2f} US$"
        )
