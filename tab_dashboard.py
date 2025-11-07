import streamlit as st
import pandas as pd

def main():
    st.header("📊 Tableau de bord")

    df = st.session_state.get("clients_df")
    if df is None or df.empty:
        st.warning("Aucune donnée disponible. Chargez un fichier dans l’onglet 📄 Fichiers.")
        return

    # 🔍 Détection automatique de la colonne Montant
    montant_col = None
    for c in df.columns:
        if "honoraires" in c.lower() or "montant" in c.lower():
            montant_col = c
            break

    if montant_col is None:
        st.error("❌ Impossible de trouver une colonne contenant 'Montant' ou 'Honoraires'.")
        st.dataframe(df.head(), use_container_width=True)
        return

    # 🧮 Nettoyage et conversion en numérique
    df[montant_col] = (
        df[montant_col]
        .astype(str)
        .str.replace(r"[^0-9\.\-]", "", regex=True)
        .replace("", "0")
        .astype(float)
    )

    # --- KPIs ---
    st.subheader("📈 Indicateurs clés")
    col1, col2, col3 = st.columns(3)
    col1.metric("👥 Nombre total de clients", len(df))
    col2.metric("💰 Montant total facturé", f"{df[montant_col].sum():,.2f} US$")
    col3.metric("💵 Montant moyen", f"{df[montant_col].mean():,.2f} US$")

    st.markdown("---")

    # --- Aperçu du tableau ---
    st.subheader("📋 Aperçu des dossiers")
    st.dataframe(df.head(10), use_container_width=True)

    # --- Graphique optionnel ---
    st.markdown("### 📊 Répartition des montants (Top 10)")
    top10 = df.nlargest(10, montant_col)
    st.bar_chart(top10.set_index(top10.columns[0])[montant_col])
