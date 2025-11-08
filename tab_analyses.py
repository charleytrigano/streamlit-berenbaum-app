import streamlit as st
import pandas as pd

def tab_analyses():
    """Onglet : Analyses et comparatifs financiers"""
    st.header("📈 Analyses financières")

    # Vérifie si les données Excel sont chargées
    if "data_xlsx" not in st.session_state or not st.session_state["data_xlsx"]:
        st.warning("⚠️ Aucune donnée disponible. Importez un fichier via l’onglet Paramètres.")
        return

    data = st.session_state["data_xlsx"]
    if "Clients" not in data:
        st.error("La feuille 'Clients' est introuvable dans le fichier Excel.")
        return

    df = data["Clients"].copy()
    df.columns = [c.strip() for c in df.columns]

    # Conversion sécurisée des montants
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

    df["Montant facturé"] = df["Montant honoraires (US $)"] + df["Autres frais (US $)"]
    df["Total payé"] = df["Acompte 1"] + df["Acompte 2"] + df["Acompte 3"] + df["Acompte 4"]
    df["Solde restant"] = df["Montant facturé"] - df["Total payé"]

    # ====== FILTRES ======
    st.markdown("### 🎯 Filtres")
    cols = st.columns(5)

    cat = cols[0].selectbox("Catégorie", options=["(Toutes)"] + sorted(df["Catégorie"].dropna().unique().tolist()) if "Catégorie" in df else ["(Toutes)"])
    souscat = cols[1].selectbox("Sous-catégorie", options=["(Toutes)"] + sorted(df["Sous-catégorie"].dropna().unique().tolist()) if "Sous-catégorie" in df else ["(Toutes)"])
    visa = cols[2].selectbox("Visa", options=["(Tous)"] + sorted(df["Visa"].dropna().unique().tolist()) if "Visa" in df else ["(Tous)"])
    annee = cols[3].selectbox("Année", options=["(Toutes)"] + sorted(df["Année"].dropna().unique().astype(str).tolist()) if "Année" in df else ["(Toutes)"])
    mois = cols[4].selectbox("Mois", options=["(Tous)"] + sorted(df["Mois"].dropna().unique().astype(str).tolist()) if "Mois" in df else ["(Tous)"])

    if cat != "(Toutes)":
        df = df[df["Catégorie"] == cat]
    if souscat != "(Toutes)":
        df = df[df["Sous-catégorie"] == souscat]
    if visa != "(Tous)":
        df = df[df["Visa"] == visa]
    if annee != "(Toutes)":
        df = df[df["Année"].astype(str) == annee]
    if mois != "(Tous)":
        df = df[df["Mois"].astype(str) == mois]

    st.markdown("---")

    # ====== SYNTHÈSE FINANCIÈRE ======
    st.subheader("💰 Synthèse financière")

    total_hon = df["Montant honoraires (US $)"].sum() if "Montant honoraires (US $)" in df else 0
    total_frais = df["Autres frais (US $)"].sum() if "Autres frais (US $)" in df else 0
    total_facture = df["Montant facturé"].sum()
    total_paye = df["Total payé"].sum()
    total_solde = df["Solde restant"].sum()

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Honoraires", f"{total_hon:,.0f} $")
    col2.metric("Autres frais", f"{total_frais:,.0f} $")
    col3.metric("Total facturé", f"{total_facture:,.0f} $")
    col4.metric("Total payé", f"{total_paye:,.0f} $")
    col5.metric("Solde restant", f"{total_solde:,.0f} $")

    st.markdown("---")

    # ====== TABLEAU DES DOSSIERS ======
    st.subheader("📋 Détail des dossiers filtrés")
    if not df.empty:
        st.dataframe(
            df[
                [
                    "Nom",
                    "Visa",
                    "Montant honoraires (US $)",
                    "Autres frais (US $)",
                    "Montant facturé",
                    "Total payé",
                    "Solde restant",
                ]
            ],
            use_container_width=True,
            height=400,
        )
    else:
        st.info("Aucun dossier ne correspond aux filtres sélectionnés.")

    st.markdown("---")

    # ====== TOP 10 CLIENTS ======
    st.subheader("🏆 Top 10 clients par montant facturé")
    if "Montant facturé" in df.columns and "Nom" in df.columns:
        top10 = (
            df.groupby("Nom")["Montant facturé"]
            .sum()
            .sort_values(ascending=False)
            .head(10)
            .reset_index()
        )

        numeric_cols = top10.select_dtypes(include=["number"]).columns
        st.dataframe(top10.style.format(subset=numeric_cols, formatter="{:,.2f}"), use_container_width=True)
    else:
        st.warning("Colonnes 'Nom' ou 'Montant facturé' manquantes pour générer le top 10.")
