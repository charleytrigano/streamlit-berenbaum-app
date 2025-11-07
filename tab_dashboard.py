import streamlit as st
import pandas as pd

def main():
    st.header("📊 Tableau de bord")

    df = st.session_state.get("clients_df")
    if df is None or df.empty:
        st.warning("Aucune donnée disponible. Chargez un fichier dans l’onglet 📄 Fichiers.")
        return

    # 🔍 Détection automatique des colonnes financières
    montant_col = None
    paye_col = None

    for c in df.columns:
        c_low = c.lower()
        if "honoraires" in c_low or ("montant" in c_low and "pay" not in c_low):
            montant_col = c
        if "pay" in c_low or "acompte" in c_low:
            paye_col = c

    if montant_col is None:
        st.error("❌ Impossible de trouver la colonne 'Montant honoraires (US $)'.")
        return

    # 🧹 Conversion en float (sécurité)
    def clean_num(s):
        try:
            return float(str(s).replace(",", "").replace("$", "").strip())
        except:
            return 0.0

    df[montant_col] = df[montant_col].map(clean_num)
    if paye_col:
        df[paye_col] = df[paye_col].map(clean_num)
    else:
        df["__PAYE__"] = 0.0
        paye_col = "__PAYE__"

    # 💰 Calcul des indicateurs
    total_facture = df[montant_col].sum()
    total_paye = df[paye_col].sum()
    solde = total_facture - total_paye

    # 📊 Petits KPI (sur une ligne compacte)
    st.markdown("### 📈 Indicateurs financiers")
    c1, c2, c3, c4 = st.columns(4)

    c1.metric("👥 Clients", f"{len(df)}")
    c2.metric("💰 Total facturé", f"{total_facture:,.2f} US$")
    c3.metric("💵 Total payé", f"{total_paye:,.2f} US$")
    c4.metric("🧾 Solde restant", f"{solde:,.2f} US$")

    st.markdown("---")

    # 📋 Tableau récapitulatif
    st.subheader("Aperçu des 10 premiers dossiers")
    st.dataframe(df.head(10), use_container_width=True)

    # 📊 Graphique top 10 clients
    st.markdown("### 📊 Top 10 des montants facturés")
    top10 = df.nlargest(10, montant_col)
    st.bar_chart(top10.set_index(top10.columns[0])[montant_col])
