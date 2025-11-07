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
