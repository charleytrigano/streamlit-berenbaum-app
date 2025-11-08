import streamlit as st
import pandas as pd

def tab_compta():
    """Onglet Comptabilité Client."""
    st.header("💳 Comptabilité client")

    if "data_xlsx" not in st.session_state or not st.session_state["data_xlsx"]:
        st.warning("⚠️ Aucune donnée chargée. Veuillez importer votre fichier Excel via l’onglet 📄 Fichiers.")
        return

    data = st.session_state["data_xlsx"]

    if "Clients" not in data:
        st.error("❌ La feuille 'Clients' est absente du fichier Excel.")
        return

    df = data["Clients"].copy()
    if df.empty:
        st.info("Aucun dossier client enregistré.")
        return

    # Nettoyage des colonnes
    df.columns = [c.strip() for c in df.columns]

    # Colonnes nécessaires
    needed = [
        "Nom", "Type visa", "Année", "Mois",
        "Montant honoraires (US $)", "Autres frais (US $)",
        "Montant facturé", "Total payé", "Solde restant"
    ]
    for col in needed:
        if col not in df.columns:
            df[col] = 0

    # Filtres
    st.markdown("### 🔍 Filtres de recherche")
    col1, col2 = st.columns(2)
    annee_list = sorted(df["Année"].dropna().unique())
    type_visa_list = sorted(df["Type visa"].dropna().unique())

    selected_annee = col1.selectbox("Année", options=["Toutes"] + list(map(str, annee_list)))
    selected_visa = col2.selectbox("Type de visa", options=["Tous"] + type_visa_list)

    df_filtre = df.copy()
    if selected_annee != "Toutes":
        df_filtre = df_filtre[df_filtre["Année"].astype(str) == selected_annee]
    if selected_visa != "Tous":
        df_filtre = df_filtre[df_filtre["Type visa"] == selected_visa]

    # Calculs
    df_filtre["Montant facturé"] = df_filtre["Montant honoraires (US $)"] + df_filtre["Autres frais (US $)"]
    total_facture = df_filtre["Montant facturé"].sum()
    total_paye = df_filtre["Total payé"].sum()
    total_solde = df_filtre["Solde restant"].sum()

    st.markdown("### 📊 Synthèse comptable")
    col1, col2, col3 = st.columns(3)
    col1.metric("💵 Total facturé", f"{total_facture:,.2f} $")
    col2.metric("💰 Total payé", f"{total_paye:,.2f} $")
    col3.metric("💸 Solde restant", f"{total_solde:,.2f} $")

    st.markdown("---")

    # Tableau détaillé
    st.subheader("📋 Détails des clients")
    affichage = df_filtre[[
        "Nom", "Type visa", "Année", "Mois",
        "Montant honoraires (US $)", "Autres frais (US $)",
        "Montant facturé", "Total payé", "Solde restant"
    ]].sort_values(by="Nom")

    st.dataframe(affichage.style.format("{:,.2f}"), use_container_width=True)

    # Export Excel
    st.markdown("---")
    st.subheader("💾 Exporter la comptabilité")
    export = st.button("📤 Télécharger le fichier Excel")

    if export:
        try:
            output_file = "Export_Compta.xlsx"
            affichage.to_excel(output_file, index=False)
            with open(output_file, "rb") as f:
                st.download_button(
                    label="📥 Télécharger le fichier comptable",
                    data=f,
                    file_name=output_file,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
        except Exception as e:
            st.error(f"Erreur lors de l’export : {e}")
