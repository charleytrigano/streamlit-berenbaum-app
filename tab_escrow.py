import streamlit as st
import pandas as pd
from common_data import ensure_loaded

def tab_escrow():
    st.header("🛡️ Escrow – Suivi des dossiers")

    data = ensure_loaded()
    if data is None or "Clients" not in data or data["Clients"].empty:
        st.info("Aucun fichier chargé.")
        return

    df = data["Clients"].copy()

    # Nettoyage des colonnes concernées
    def to_float(x):
        try:
            return float(str(x).replace(",", ".").replace(" ", ""))
        except Exception:
            return 0.0

    df["Acompte 1"] = df["Acompte 1"].apply(to_float)
    df["Montant honoraires (US $)"] = df["Montant honoraires (US $)"].apply(to_float)
    if "Escrow" not in df.columns:
        df["Escrow"] = False

    # Escrow bool vers bool pur (True/False/1/0/Vrai/Faux/etc)
    def escrow_bool(val):
        str_val = str(val).strip().lower()
        return str_val in ("true", "vrai", "1", "oui", "yes")

    df["Escrow"] = df["Escrow"].apply(escrow_bool)

    # Filtre 1 : Escrow (case cochée)
    mask_escrow = df["Escrow"] == True
    # Filtre 2 : Montant honoraires = 0 et acompte 1 > 0 (règle métier)
    mask_auto = (df["Montant honoraires (US $)"] == 0) & (df["Acompte 1"] > 0)

    # Union des deux filtres (tous les dossiers qui remplissent l'un ou l'autre)
    escrow_df = df[mask_escrow | mask_auto].copy()

    if escrow_df.empty:
        st.info("Aucun dossier en Escrow pour le moment.")
        return

    # Montant escrow = Acompte 1 dans tous les cas
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
