import streamlit as st
import pandas as pd
from datetime import datetime

EXCEL_FILE = "Clients BL.xlsx"

def save_to_excel(data_dict):
    """Sauvegarde les feuilles Excel après mise à jour."""
    try:
        with pd.ExcelWriter(EXCEL_FILE, engine="openpyxl", mode="w") as writer:
            for sheet_name, df in data_dict.items():
                df.to_excel(writer, index=False, sheet_name=sheet_name)
        st.success("💾 Fichier Excel mis à jour avec succès.")
        return True
    except Exception as e:
        st.error(f"Erreur lors de la sauvegarde : {e}")
        return False


def tab_escrow():
    """Onglet de gestion des dossiers Escrow."""
    st.header("🛡️ Gestion des dossiers Escrow")

    if "data_xlsx" not in st.session_state or not st.session_state["data_xlsx"]:
        st.warning("⚠️ Aucune donnée chargée. Veuillez importer le fichier Excel via l’onglet 📄 Fichiers.")
        return

    data = st.session_state["data_xlsx"]
    df_escrow = data.get("Escrow", pd.DataFrame())

    if df_escrow.empty:
        st.info("Aucun dossier Escrow enregistré.")
        return

    df_escrow.columns = [c.strip() for c in df_escrow.columns]
    if "État" not in df_escrow.columns:
        df_escrow["État"] = "À réclamer"

    st.markdown("### 📋 Liste des dossiers Escrow")

    # Séparer les états
    a_reclamer = df_escrow[df_escrow["État"] == "À réclamer"]
    reclames = df_escrow[df_escrow["État"] == "Réclamé"]
    regles = df_escrow[df_escrow["État"] == "Réglé"]

    tab1, tab2, tab3 = st.tabs(["💰 À réclamer", "📨 Réclamés", "✅ Réglés"])

    with tab1:
        st.subheader("💰 Dossiers à réclamer")
        if not a_reclamer.empty:
            st.dataframe(a_reclamer, use_container_width=True)
        else:
            st.info("Aucun dossier à réclamer.")

    with tab2:
        st.subheader("📨 Dossiers réclamés")
        if not reclames.empty:
            st.dataframe(reclames, use_container_width=True)
        else:
            st.info("Aucun dossier réclamé.")

    with tab3:
        st.subheader("✅ Dossiers réglés")
        if not regles.empty:
            st.dataframe(regles, use_container_width=True)
        else:
            st.info("Aucun dossier réglé.")

    st.markdown("---")

    # === ACTION : marquer comme réclamé ===
    st.markdown("### ✉️ Marquer un dossier comme réclamé")
    nom = st.text_input("Nom du client")
    if st.button("📨 Marquer comme réclamé"):
        if nom in df_escrow["Nom"].values:
            df_escrow.loc[df_escrow["Nom"] == nom, ["État", "Date réclamation"]] = ["Réclamé", datetime.now().strftime("%d/%m/%Y")]
            data["Escrow"] = df_escrow
            if save_to_excel(data):
                st.session_state["data_xlsx"] = data
                st.success(f"✅ Dossier {nom} marqué comme réclamé.")
                st.experimental_rerun()
        else:
            st.warning("Nom introuvable dans la liste Escrow.")

    st.markdown("---")

    # === ACTION : marquer comme réglé ===
    st.markdown("### 💵 Marquer un dossier comme réglé")
    nom2 = st.text_input("Nom du client à marquer comme réglé")
    if st.button("💵 Marquer comme réglé"):
        if nom2 in df_escrow["Nom"].values:
            df_escrow.loc[df_escrow["Nom"] == nom2, ["État", "Date règlement"]] = ["Réglé", datetime.now().strftime("%d/%m/%Y")]
            data["Escrow"] = df_escrow
            if save_to_excel(data):
                st.session_state["data_xlsx"] = data
                st.success(f"💰 Dossier {nom2} marqué comme réglé.")
                st.experimental_rerun()
        else:
            st.warning("Nom introuvable dans la liste Escrow.")
