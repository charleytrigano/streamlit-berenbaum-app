import streamlit as st
import pandas as pd

def main():
    st.header("📊 Tableau de bord")

    df = st.session_state.get("clients_df")
    if df is None or df.empty:
        st.warning("Aucune donnée disponible. Chargez un fichier dans l’onglet 📄 Fichiers.")
        return

    # --- Détection de la colonne de montant ---
    montant_col = None
    for c in df.columns:
        if "honoraires" in c.lower() or "montant" in c.lower():
            montant_col = c
            break

    # --- KPIs ---
    st.subheader("📈 Indicateurs clés")
    col1, col2, col3 = st.columns(3)
    col1.metric("👥 Nombre total de clients", len(df))
    if montant_col:
        col2.metric("💰 Montant total facturé", f"{df[montant_col].sum():,.2f} US$")
        col3.metric("💵 Montant moyen", f"{df[montant_col].mean():,.2f} US$")
    else:
        col2.warning("Colonne 'Montant honoraires (US $)' introuvable.")
        col3.empty()

    st.markdown("---")

    # --- Aperçu des 10 premières lignes ---
    st.subheader("📋 Aperçu des dossiers")
    st.dataframe(df.head(10), use_container_width=True)
