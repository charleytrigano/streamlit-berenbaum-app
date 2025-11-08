import streamlit as st
import pandas as pd

def tab_analyses():
    """Analyses et comparatifs financiers (tableaux, top 10)."""
    st.header("📈 Analyses financières")

    if "data_xlsx" not in st.session_state or not st.session_state["data_xlsx"]:
        st.warning("⚠️ Aucune donnée disponible. Chargez le fichier via l’onglet 📄 Fichiers.")
        return

    data = st.session_state["data_xlsx"]

    if "Clients" not in data:
        st.error("❌ La feuille 'Clients' est absente du fichier Excel.")
        return

    df = data["Clients"].copy()
    if df.empty:
        st.warning("📄 La feuille 'Clients' est vide.")
        return

    # Normaliser les colonnes
    df.columns = [c.strip() for c in df.columns]

    # Colonnes nécessaires
    needed = [
        "Nom", "Année", "Mois",
        "Montant honoraires (US $)", "Autres frais (US $)",
        "Acompte 1", "Acompte 2", "Acompte 3", "Acompte 4"
    ]
    for col in needed:
        if col not in df.columns:
            df[col] = 0

    df["Montant facturé"] = df["Montant honoraires (US $)"] + df["Autres frais (US $)"]
    df["Total payé"] = df[["Acompte 1", "Acompte 2", "Acompte 3", "Acompte 4"]].sum(axis=1)
    df["Solde restant"] = df["Montant facturé"] - df["Total payé"]

    # ========================= FILTRES =========================
    st.markdown("### 🔍 Sélection des périodes de comparaison")

    col1, col2 = st.columns(2)
    liste_annees = sorted(df["Année"].dropna().unique())
    annee1 = col1.selectbox("Période 1 (Année)", liste_annees, index=0 if liste_annees else None)
    annee2 = col2.selectbox("Période 2 (Année)", liste_annees, index=1 if len(liste_annees) > 1 else 0)

    # Comparatif simple entre deux années
    if annee1 and annee2:
        df1 = df[df["Année"] == annee1]
        df2 = df[df["Année"] == annee2]

        synthese = pd.DataFrame({
            "Période": [annee1, annee2],
            "Montant facturé": [df1["Montant facturé"].sum(), df2["Montant facturé"].sum()],
            "Total payé": [df1["Total payé"].sum(), df2["Total payé"].sum()],
            "Solde restant": [df1["Solde restant"].sum(), df2["Solde restant"].sum()]
        })

        st.markdown("### 📊 Comparatif entre les périodes")
        st.dataframe(synthese.style.format("{:,.2f}"))

    st.markdown("---")

    # ========================= TOP 10 =========================
    st.markdown("### 🏆 Top 10 clients")

    top_choice = st.radio(
        "Classement par :",
        ["Montant facturé", "Total payé", "Solde restant"],
        horizontal=True
    )

    top10 = df.groupby("Nom", as_index=False)[top_choice].sum().sort_values(by=top_choice, ascending=False).head(10)
    top10.index = range(1, len(top10) + 1)

    st.dataframe(top10.style.format("{:,.2f}"), use_container_width=True)
