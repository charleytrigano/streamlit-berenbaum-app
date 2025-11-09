import streamlit as st
import pandas as pd

def tab_dashboard():
    """Tableau de bord principal - synthèse financière."""
    st.header("📊 Tableau de bord")

    # Vérifie si les données Excel sont chargées
    if "data_xlsx" not in st.session_state or not st.session_state["data_xlsx"]:
        st.warning("⚠️ Aucune donnée disponible. Chargez d'abord le fichier Excel via l'onglet 📄 Fichiers.")
        return

    data = st.session_state["data_xlsx"]

    # Vérifie la présence de la feuille "Clients"
    if "Clients" not in data:
        st.error("❌ La feuille 'Clients' est absente du fichier Excel.")
        return

    df = data["Clients"].copy()
    if df.empty:
        st.warning("📄 La feuille 'Clients' est vide.")
        return

    # === Nettoyage des montants ===
    def _to_float(x):
        try:
            s = str(x).replace(",", ".").replace("\u00A0", "").strip()
            return float(s) if s not in ["", "nan", "None"] else 0.0
        except:
            return 0.0

    if "Montant honoraires (US $)" in df.columns:
        df["Montant honoraires (US $)"] = df["Montant honoraires (US $)"].map(_to_float)
    else:
        df["Montant honoraires (US $)"] = 0.0

    if "Autres frais (US $)" in df.columns:
        df["Autres frais (US $)"] = df["Autres frais (US $)"].map(_to_float)
    else:
        df["Autres frais (US $)"] = 0.0

    df["Montant facturé"] = df["Montant honoraires (US $)"] + df["Autres frais (US $)"]

    acompte_cols = [c for c in df.columns if c.lower().startswith("acompte")]
    for c in acompte_cols:
        df[c] = df[c].map(_to_float)

    df["Total payé"] = df[acompte_cols].sum(axis=1)
    df["Solde restant"] = df["Montant facturé"] - df["Total payé"]

    # === Formatage monétaire ===
    def _fmt_money(v):
        try:
            return f"{v:,.2f}".replace(",", " ").replace(".", ",") + " $"
        except:
            return v

    # === KPI principaux ===
    total_dossiers = len(df)
    total_facture = df["Montant facturé"].sum()
    total_paye = df["Total payé"].sum()
    total_solde = df["Solde restant"].sum()

    st.markdown("### 📈 Synthèse financière")

    kpi_style = """
    <style>
    [data-testid="stMetricValue"] {
        font-size: 22px !important;
        color: #fafafa !important;
    }
    </style>
    """
    st.markdown(kpi_style, unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📂 Dossiers", f"{total_dossiers:,}".replace(",", " "))
    c2.metric("💵 Montant facturé", _fmt_money(total_facture))
    c3.metric("💰 Total payé", _fmt_money(total_paye))
    c4.metric("📉 Solde restant", _fmt_money(total_solde))

    st.markdown("---")

    # === Tableau récapitulatif ===
    st.subheader("📋 Détails des dossiers clients")
    df_display = df[[
        "Dossier N", "Nom", "Catégories", "Sous-catégories", "Visa",
        "Montant honoraires (US $)", "Autres frais (US $)",
        "Montant facturé", "Total payé", "Solde restant"
    ]].copy()

    # Application du format monétaire
    for col in ["Montant honoraires (US $)", "Autres frais (US $)", "Montant facturé", "Total payé", "Solde restant"]:
        df_display[col] = df_display[col].map(_fmt_money)

    st.dataframe(df_display, use_container_width=True, height=400)
