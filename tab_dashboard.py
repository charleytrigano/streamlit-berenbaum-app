import streamlit as st
import pandas as pd

def main():
    st.header("📊 Tableau de bord")

    df = st.session_state.get("clients_df")
    if df is None or df.empty:
        st.warning("Aucune donnée disponible. Chargez un fichier dans l’onglet 📄 Fichiers.")
        return

    # ✅ Colonnes nécessaires
    required_cols = [
        "Nom",
        "Montant honoraires (US $)",
        "Autres frais (US $)",
        "Acompte 1",
        "Acompte 2",
        "Acompte 3",
        "Acompte 4"
    ]
    for col in required_cols:
        if col not in df.columns:
            st.error(f"❌ Colonne manquante : '{col}'")
            return

    # 🧮 Conversion propre en float
    def to_float(x):
        try:
            return float(str(x).replace(",", "").replace("$", "").strip())
        except:
            return 0.0

    for col in required_cols[1:]:
        df[col] = df[col].map(to_float)

    # 📊 Calculs globaux
    df["Montant facturé"] = df["Montant honoraires (US $)"] + df["Autres frais (US $)"]
    df["Total payé"] = df["Acompte 1"] + df["Acompte 2"] + df["Acompte 3"] + df["Acompte 4"]
    df["Solde restant"] = df["Montant facturé"] - df["Total payé"]

    # --- Agrégats sur TOUT le fichier ---
    total_clients = len(df)
    total_facture = df["Montant facturé"].sum()
    total_paye = df["Total payé"].sum()
    solde_restant = df["Solde restant"].sum()

    # 📈 KPIs compactes
    st.markdown("### 📈 Indicateurs financiers")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("👥 Clients", f"{total_clients}")
    col2.metric("💰 Montant facturé", f"{total_facture:,.2f} US$")
    col3.metric("💵 Total payé", f"{total_paye:,.2f} US$")
    col4.metric("🧾 Solde restant", f"{solde_restant:,.2f} US$")

    st.markdown("---")

    # 📋 Tableau complet (tout le fichier)
    st.subheader("📋 Liste complète des dossiers")
    st.dataframe(
        df[
            [
                "Nom",
                "Montant honoraires (US $)",
                "Autres frais (US $)",
                "Montant facturé",
                "Total payé",
                "Solde restant"
            ]
        ],
        use_container_width=True,
        hide_index=True
    )

    # 📊 Graphique top 10
    st.markdown("### 📊 Top 10 des clients par montant facturé")
    top10 = df.nlargest(10, "Montant facturé")
    st.bar_chart(top10.set_index("Nom")["Montant facturé"])
