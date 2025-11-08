import streamlit as st
import pandas as pd

def tab_compta():
    """Onglet : Comptabilité Client"""
    st.header("💳 Comptabilité Client")

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

    # Conversion des colonnes numériques
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

    # Calculs principaux
    df["Montant facturé"] = df["Montant honoraires (US $)"] + df["Autres frais (US $)"]
    df["Total payé"] = df["Acompte 1"] + df["Acompte 2"] + df["Acompte 3"] + df["Acompte 4"]
    df["Solde restant"] = df["Montant facturé"] - df["Total payé"]

    # ================== FILTRES ==================
    st.markdown("### 🎯 Filtres")
    c1, c2, c3 = st.columns(3)
    visa = c1.selectbox(
        "Visa",
        options=["(Tous)"] + sorted(df["Visa"].dropna().unique().tolist()) if "Visa" in df else ["(Tous)"],
        key="compta_visa"
    )
    annee = c2.selectbox(
        "Année",
        options=["(Toutes)"] + sorted(df["Année"].dropna().unique().astype(str).tolist()) if "Année" in df else ["(Toutes)"],
        key="compta_annee"
    )
    mois = c3.selectbox(
        "Mois",
        options=["(Tous)"] + sorted(df["Mois"].dropna().unique().astype(str).tolist()) if "Mois" in df else ["(Tous)"],
        key="compta_mois"
    )

    # Application des filtres
    if visa != "(Tous)":
        df = df[df["Visa"] == visa]
    if annee != "(Toutes)":
        df = df[df["Année"].astype(str) == annee]
    if mois != "(Tous)":
        df = df[df["Mois"].astype(str) == mois]

    st.markdown("---")

    # ================== SYNTHÈSE ==================
    st.subheader("📊 Synthèse financière")
    total_facture = df["Montant facturé"].sum()
    total_paye = df["Total payé"].sum()
    total_solde = df["Solde restant"].sum()

    c1, c2, c3 = st.columns(3)
    c1.metric("Facturé", f"{total_facture:,.0f} $")
    c2.metric("Payé", f"{total_paye:,.0f} $")
    c3.metric("Solde", f"{total_solde:,.0f} $")

    st.markdown("---")

    # ================== TABLEAU DÉTAILLÉ ==================
    st.subheader("📋 Détail par client")
    colonnes_aff = [
        "Nom",
        "Visa",
        "Montant honoraires (US $)",
        "Autres frais (US $)",
        "Montant facturé",
        "Total payé",
        "Solde restant",
    ]
    affichage = df[colonnes_aff] if all(c in df.columns for c in colonnes_aff) else df

    numeric_cols = affichage.select_dtypes(include=["number"]).columns
    st.dataframe(
        affichage.style.format(subset=numeric_cols, formatter="{:,.2f}"),
        use_container_width=True,
        height=450,
    )

    st.markdown("---")

    # ================== SYNTHÈSE PAR VISA ==================
    st.subheader("🗂️ Synthèse par type de visa")
    if "Visa" in df.columns:
        recap_visa = (
            df.groupby("Visa")[["Montant facturé", "Total payé", "Solde restant"]]
            .sum()
            .sort_values("Montant facturé", ascending=False)
            .reset_index()
        )
        numeric_cols = recap_visa.select_dtypes(include=["number"]).columns
        st.dataframe(
            recap_visa.style.format(subset=numeric_cols, formatter="{:,.2f}"),
            use_container_width=True,
        )
    else:
        st.info("Aucune colonne 'Visa' trouvée pour regrouper les données.")

    st.markdown("---")

    # ================== SYNTHÈSE PAR ANNÉE ==================
    st.subheader("📅 Synthèse par année")
    if "Année" in df.columns:
        recap_annee = (
            df.groupby("Année")[["Montant facturé", "Total payé", "Solde restant"]]
            .sum()
            .sort_index(ascending=True)
            .reset_index()
        )
        numeric_cols = recap_annee.select_dtypes(include=["number"]).columns
        st.dataframe(
            recap_annee.style.format(subset=numeric_cols, formatter="{:,.2f}"),
            use_container_width=True,
        )
    else:
        st.info("Aucune colonne 'Année' trouvée pour la synthèse temporelle.")
