import streamlit as st
import pandas as pd

def tab_escrow():
    st.header("🛡️ Escrow")

    if "data_xlsx" not in st.session_state or st.session_state["data_xlsx"] is None:
        st.warning("Fichier non chargé — veuillez l'importer via l’onglet 📄 Fichiers.")
        return

    df_clients = st.session_state["data_xlsx"].get("Clients")

    if df_clients is None:
        st.error("La feuille 'Clients' est manquante dans le fichier Excel.")
        return

    # ---- NORMALISATION DE LA COLONNE ESCROW ----
    if "Escrow" not in df_clients.columns:
        st.error("La colonne 'Escrow' est absente du fichier Excel.")
        return

    # Convertir toute valeur Excel en vrai booléen
    def to_bool(v):
        if isinstance(v, bool):
            return v
        if isinstance(v, (int, float)):
            return v == 1
        if isinstance(v, str):
            return v.strip().lower() in ["true", "vrai", "1", "yes", "oui"]
        return False

    df_clients["Escrow"] = df_clients["Escrow"].apply(to_bool)

    # ---- CONDITION D'AFFICHAGE DES DOSSIERS ESCROW ----
    df_escrow = df_clients[
        (df_clients["Escrow"] == True)
        | (
            pd.to_numeric(df_clients["Acompte 1"], errors="coerce").fillna(0) > 0
        ) & (
            pd.to_numeric(df_clients["Montant honoraires (US $)"], errors="coerce").fillna(0) == 0
        )
    ]

    # ---- SI AUCUN DOSSIER ----
    if df_escrow.empty:
        st.info("Aucun dossier en Escrow pour le moment.")
        return

    # ---- AFFICHAGE ----
    st.subheader("Dossiers en Escrow")

    montant_total = df_escrow["Acompte 1"].fillna(0).sum()

    st.metric("Montant total", f"{montant_total:,.2f} $")

    st.dataframe(df_escrow.reset_index(drop=True))

