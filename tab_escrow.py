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
    df["Acompte 2"] = df["Acompte 2"].apply(to_float) if "Acompte 2" in df.columns else 0
    df["Acompte 3"] = df["Acompte 3"].apply(to_float) if "Acompte 3" in df.columns else 0
    df["Acompte 4"] = df["Acompte 4"].apply(to_float) if "Acompte 4" in df.columns else 0
    df["Montant honoraires (US $)"] = df["Montant honoraires (US $)"].apply(to_float)
    if "Escrow" not in df.columns:
        df["Escrow"] = False

    # --- CONDITIONS escrow selon tes règles métier ---
    # Cas 1 : case cochée
    escrow_checked = df["Escrow"] == True
    # Cas 2 : honoraires à zéro + acompte 1 > 0 + case non cochée
    escrow_auto = (
        (df["Montant honoraires (US $)"] == 0) &
        (df["Acompte 1"] > 0) &
        ((df["Escrow"] == False) | (df["Escrow"].isna()))
    )

    # Sélectionne dossiers escrow
    escrow_mask = escrow_checked | escrow_auto
    escrow_df = df[escrow_mask].copy()

    if escrow_df.empty:
        st.info("Aucun dossier en Escrow pour le moment.")
        return

    # Le montant de l'Escrow est TOUJOURS égal à Acompte 1 selon la règle métier
    escrow_df["Montant escrow"] = escrow_df["Acompte 1"]

    st.subheader("📋 Dossiers détectés en Escrow")
    st.dataframe(
        escrow_df[
            [
                "Dossier N",
                "Nom",
                "Acompte 1",
                "Montant escrow",
                "Escrow"
            ]
        ],
        use_container_width=True
    )
