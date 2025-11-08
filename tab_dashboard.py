import streamlit as st
import pandas as pd

def tab_dashboard():
    """Tableau de bord principal - synthèse financière."""
    st.header("📊 Tableau de bord")

    # Vérifier si les données Excel sont chargées
    if "data_xlsx" not in st.session_state or not st.session_state["data_xlsx"]:
        st.warning("⚠️ Aucune donnée disponible. Chargez d'abord le fichier Excel via l'onglet '📄 Fichiers'.")
        return

    data = st.session_state["data_xlsx"]

    # Vérifier la présence de la feuille "Clients"
    if "Clients" not in data:
        st.error("❌ La feuille 'Clients' est absente du fichier Excel.")
        return

    df = data["Clients"].copy()

    if df.empty:
        st.warning("📄 La feuille 'Clients' est vide.")
        return

    # Normaliser les colonnes
    df.columns = [c.strip() for c in df.columns]

    # Vérifier les colonnes nécessaires
    required_cols = [
        "Montant honoraires (US $)",
        "Autres frais (US $)",
        "Acompte 1",
        "Acompte 2",
        "Acompte 3",
        "Acompte 4",
    ]
    for col in required_cols:
        if col not in df.columns:
            df[col] = 0

    # Calculs
    df["Montant facturé"] = df["Montant honoraires (US $)"] + df["Autres frais (US $)"]
    df["Total payé"] = df[["Acompte 1", "Acompte 2", "Acompte 3", "Acompte 4"]].sum(axis=1)
    df["Solde restant"] = df["Montant facturé"] - df["Total payé"]

    total_facture = df["Montant facturé"].sum()
    total_paye = df["Total payé"].sum()
    solde = df["Solde restant"].sum()

    # ===================== KPI =====================
    st.markdown("### Synthèse financière")

    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric("💰 Montant facturé", f"{total_facture:,.2f} $")
    kpi2.metric("✅ Total payé", f"{total_paye:,.2f} $")
    kpi3.metric("💼 Solde restant", f"{solde:,.2f} $")

    st.markdown("---")

    # ===================== Filtres =====================
    st.markdown("### 🔍 Filtres")

    col1, col2 = st.columns(2)
    filtre_annee = col1.selectbox("Année", sorted(df["Année"].dropna().unique()) if "Année" in df else [], index=None, placeholder="Toutes")
    filtre_visa = col2.selectbox("Type de Visa", sorted(df["Type visa"].dropna().unique()) if "Type visa" in df else [], index=None, placeholder="Tous")

    # Appliquer les filtres
    df_filtre = df.copy()
    if filtre_annee:
        df_filtre = df_filtre[df_filtre["Année"] == filtre_annee]
    if filtre_visa:
        df_filtre = df_filtre[df_filtre["Type visa"] == filtre_visa]

    # ===================== Tableau principal =====================
    st.markdown("### 📋 Dossiers Clients")

    colonnes_affichees = [
        "Nom",
        "Type visa" if "Type visa" in df.columns else None,
        "Montant facturé",
        "Total payé",
        "Solde restant",
    ]
    colonnes_affichees = [c for c in colonnes_affichees if c in df_filtre.columns]

    st.dataframe(df_filtre[colonnes_affichees], use_container_width=True, height=500)
