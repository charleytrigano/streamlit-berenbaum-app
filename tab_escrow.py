import streamlit as st
import pandas as pd
from common_data import ensure_loaded

def tab_escrow():
    st.header("🛡️ Escrow – Suivi des dossiers")

    data = ensure_loaded()
    if data is None:
        st.warning("Aucun fichier chargé.")
        return

    if "Clients" not in data:
        st.error("La feuille 'Clients' est absente.")
        return

    df = data["Clients"].copy()

    # --- Nettoyage automatique ---
    def to_float(x):
        try:
            return float(str(x).replace(",", ".").replace(" ", ""))
        except:
            return 0.0

    df["Acompte 1"] = df["Acompte 1"].apply(to_float)
    df["Montant honoraires (US $)"] = df["Montant honoraires (US $)"].apply(to_float)
    if "Escrow" not in df.columns:
        df["Escrow"] = False

    # --- Recherche Escrow ---
    # Cas 1 : case cochée
    mask_escrow = df["Escrow"] == True

    # Cas 2 : Montant honoraires à 0 et acompte 1 > 0
    mask_auto = (df["Montant honoraires (US $)"] == 0) & (df["Acompte 1"] > 0)

    # Union des deux cas
    escrow_df = df[mask_escrow | mask_auto].copy()
    if escrow_df.empty:
        st.info("Aucun dossier en Escrow pour le moment.")
        return

    # Dans tous les cas le montant escrow = acompte 1
    escrow_df["Montant escrow"] = escrow_df["Acompte 1"]

    st.subheader("📋 Dossiers détectés en Escrow")
    st.dataframe(
        escrow_df[
            [
                "Dossier N",
                "Nom",
                "Montant honoraires (US $)",
                "Acompte 1",
                "Montant escrow",
                "Escrow"
            ]
        ],
        use_container_width=True
    )
