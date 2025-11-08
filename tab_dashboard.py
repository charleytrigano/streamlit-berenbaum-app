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

    # Nettoyage des noms de colonnes
    df.columns = [c.strip() for c in df.columns]

    # Conversion en numérique des colonnes utiles
    numeric_cols = [
        "Montant honoraires (US $)",
        "Autres frais (US $)",
        "Acompte 1",
        "Acompte 2",
        "Acompte 3",
        "Acompte 4",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # Calculs principaux
    df["Montant facturé"] = df["Montant honoraires (US $)"] + df["Autres frais (US $)"]
    df["Total payé"] = df["Acompte 1"] + df["Acompte 2"] + df["Acompte 3"] + df["Acompte 4"]
    df["Solde restant"] = df["Montant facturé"] - df["Total payé"]

    # ================= FILTRES =================
    st.markdown("### 🎯 Filtres")
    col1, col2, col3, col4, col5 = st.columns(5)

    categorie = col1.selectbox(
        "Catégorie",
        ["(Toutes)"] + sorted(df["Catégorie"].dropna().unique().tolist()) if "Catégorie" in df else ["(Toutes)"],
        key="dash_cat"
    )
    souscat = col2.selectbox(
        "Sous-catégorie",
        ["(Toutes)"] + sorted(df["Sous-catégorie"].dropna().unique().tolist()) if "Sous-catégorie" in df else ["(Toutes)"],
        key="dash_souscat"
    )
    visa = col3.selectbox(
        "Visa",
        ["(Tous)"] + sorted(df["Visa"].dropna().unique().tolist()) if "Visa" in df else ["(Tous)"],
        key="dash_visa"
    )
    annee = col4.selectbox(
        "Année",
        ["(Toutes)"] + sorted(df["Année"].dropna().unique().astype(str).tolist()) if "Année" in df else ["(Toutes)"],
        key="dash_annee"
    )
    mois = col5.selectbox(
        "Mois",
        ["(Tous)"] + sorted(df["Mois"].dropna().unique().astype(str).tolist()) if "Mois" in df else ["(Tous)"],
        key="dash_mois"
    )

    # Application des filtres
    if categorie != "(Toutes)":
        df = df[df["Catégorie"] == categorie]
    if souscat != "(Toutes)":
        df = df[df["Sous-catégorie"] == souscat]
    if visa != "(Tous)":
        df = df[df["Visa"] == visa]
    if annee != "(Toutes)":
        df = df[df["Année"].astype(str) == annee]
    if mois != "(Tous)":
        df = df[df["Mois"].astype(str) == mois]

    st.markdown("---")

    # ================= SYNTHÈSE FINANCIÈRE =================
    st.subheader("📊 Synthèse financière")

    total_honoraire = df["Montant honoraires (US $)"].sum()
    total_autres = df["Autres frais (US $)"].sum()
    total_facture = df["Montant facturé"].sum()
    total_paye = df["Total payé"].sum()
    total_solde = df["Solde restant"].sum()

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Honoraires", f"{total_honoraire:,.0f} $")
    c2.metric("Autres frais", f"{total_autres:,.0f} $")
    c3.metric("Facturé", f"{total_facture:,.0f} $")
    c4.metric("Payé", f"{total_paye:,.0f} $")
    c5.metric("Solde", f"{total_solde:,.0f} $")

    st.markdown("---")

    # ================= TABLEAU DES CLIENTS =================
    st.subheader("📋 Dossiers clients")
    colonnes_aff = [
        "Nom",
        "Visa",
        "Montant honoraires (US $)",
        "Autres frais (US $)",
        "Montant facturé",
        "Total payé",
        "Solde restant",
    ]
    if all(c in df.columns for c in colonnes_aff):
        numeric_cols = df[colonnes_aff].select_dtypes(include=["number"]).columns
        st.dataframe(
            df[colonnes_aff].style.format(subset=numeric_cols, formatter="{:,.2f}"),
            use_container_width=True,
            height=400,
        )
    else:
        st.info("Certaines colonnes sont manquantes dans le fichier.")

    st.markdown("---")

    # ================= TOP 10 CLIENTS =================
    st.subheader("🏆 Top 10 des dossiers (par montant facturé)")
    top10 = df.nlargest(10, "Montant facturé")[["Nom", "Visa", "Montant facturé", "Total payé", "Solde restant"]]
    numeric_cols = top10.select_dtypes(include=["number"]).columns
    st.dataframe(
        top10.style.format(subset=numeric_cols, formatter="{:,.2f}"),
        use_container_width=True,
        height=400,
    )

    st.markdown("— Fin du tableau de bord —")
