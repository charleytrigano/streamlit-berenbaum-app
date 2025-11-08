import streamlit as st
import pandas as pd

def tab_analyses():
    """Onglet Analyses - comparaison et synthèse avancée."""
    st.header("📈 Analyses et comparatifs")

    # Vérifier si les données Excel sont chargées
    if "data_xlsx" not in st.session_state or not st.session_state["data_xlsx"]:
        st.warning("⚠️ Aucune donnée disponible. Chargez d'abord le fichier Excel via l'onglet '📄 Fichiers'.")
        return

    data = st.session_state["data_xlsx"]

    if "Clients" not in data:
        st.error("❌ La feuille 'Clients' est absente du fichier Excel.")
        return

    df = data["Clients"].copy()
    if df.empty:
        st.warning("📄 La feuille 'Clients' est vide.")
        return

    df.columns = [c.strip() for c in df.columns]

    # Conversion des colonnes en numériques
    montant_cols = [
        "Montant honoraires (US $)",
        "Autres frais (US $)",
        "Acompte 1",
        "Acompte 2",
        "Acompte 3",
        "Acompte 4",
    ]
    for col in montant_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # Calculs financiers
    df["Montant facturé"] = df["Montant honoraires (US $)"] + df["Autres frais (US $)"]
    df["Total payé"] = df["Acompte 1"] + df["Acompte 2"] + df["Acompte 3"] + df["Acompte 4"]
    df["Solde restant"] = df["Montant facturé"] - df["Total payé"]

    # ===================== FILTRES =====================
    st.markdown("### 🎯 Filtres d'analyse")
    col1, col2, col3, col4 = st.columns(4)

    visa = col1.selectbox(
        "Visa",
        ["(Tous)"] + sorted(df["Visa"].dropna().unique().tolist()) if "Visa" in df else ["(Tous)"],
        key="ana_visa"
    )
    annee = col2.selectbox(
        "Année",
        ["(Toutes)"] + sorted(df["Année"].dropna().unique().astype(str).tolist()) if "Année" in df else ["(Toutes)"],
        key="ana_annee"
    )
    mois = col3.selectbox(
        "Mois",
        ["(Tous)"] + sorted(df["Mois"].dropna().unique().astype(str).tolist()) if "Mois" in df else ["(Tous)"],
        key="ana_mois"
    )
    comparaison = col4.selectbox(
        "Comparer par",
        ["Visa", "Année", "Mois", "Catégorie", "Sous-catégorie"],
        key="ana_compare"
    )

    # Application des filtres
    if visa != "(Tous)":
        df = df[df["Visa"] == visa]
    if annee != "(Toutes)":
        df = df[df["Année"].astype(str) == annee]
    if mois != "(Tous)":
        df = df[df["Mois"].astype(str) == mois]

    st.markdown("---")

    # ===================== KPI GLOBAUX =====================
    st.subheader("📊 Synthèse financière")
    total_facture = df["Montant facturé"].sum()
    total_paye = df["Total payé"].sum()
    total_solde = df["Solde restant"].sum()

    c1, c2, c3 = st.columns(3)
    c1.metric("Total facturé", f"{total_facture:,.0f} $")
    c2.metric("Total payé", f"{total_paye:,.0f} $")
    c3.metric("Solde restant", f"{total_solde:,.0f} $")

    st.markdown("---")

    # ===================== ANALYSE PAR CRITÈRE =====================
    st.subheader(f"🔍 Analyse par {comparaison}")
    if comparaison in df.columns:
        analyse = (
            df.groupby(comparaison)[["Montant facturé", "Total payé", "Solde restant"]]
            .sum()
            .sort_values("Montant facturé", ascending=False)
            .reset_index()
        )

        numeric_cols = analyse.select_dtypes(include=["number"]).columns
        st.dataframe(
            analyse.style.format(subset=numeric_cols, formatter="{:,.2f}"),
            use_container_width=True,
            height=400,
        )
    else:
        st.info(f"La colonne '{comparaison}' n'existe pas dans le fichier Excel.")

    st.markdown("---")

    # ===================== TOP 10 =====================
    st.subheader("🏆 Top 10 des clients (par montant facturé)")
    top10 = df.nlargest(10, "Montant facturé")[["Nom", "Visa", "Montant facturé", "Total payé", "Solde restant"]]
    numeric_cols = top10.select_dtypes(include=["number"]).columns
    st.dataframe(
        top10.style.format(subset=numeric_cols, formatter="{:,.2f}"),
        use_container_width=True,
        height=400,
    )

    st.markdown("— Fin des analyses —")
