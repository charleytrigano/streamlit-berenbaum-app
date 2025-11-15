import streamlit as st
import pandas as pd
import numpy as np
from common_data import ensure_loaded

def tab_escrow():
    st.header("🛡️ Escrow – Suivi des dossiers")

    data = ensure_loaded()
    if data is None or "Clients" not in data or data["Clients"].empty:
        st.info("Aucun fichier chargé.")
        return

    df = data["Clients"].copy()

    def to_float(x):
        try:
            f = float(str(x).replace(",", ".").replace(" ", ""))
            # Considère 'None' ou '' ou 'nan' ou pd.NA ou np.nan ou 'NoneType' comme zero aussi
            if (str(x).strip().lower() in ["none", "nan", "", "nonetype"] or pd.isna(x)):
                return 0.0
            return f
        except Exception:
            return 0.0

    df["Montant honoraires (US $)"] = df["Montant honoraires (US $)"].apply(to_float)
    df["Acompte 1"] = df["Acompte 1"].apply(to_float)
    if "Escrow" not in df.columns:
        df["Escrow"] = False

    # Nettoyage Escrow : True, Vrai, Oui, 1, X, etc.
    def escrow_bool(val):
        val = str(val).strip().lower()
        return val in ["true", "vrai", "1", "oui", "x", "ok"]

    df["Escrow"] = df["Escrow"].apply(escrow_bool)

    # Cas 1 : Escrow est coché/vrai/etc (mask_escrow)
    mask_escrow = df["Escrow"] == True
    
    # Cas 2 : honoraires zéro/absent et acompte 1 > 0 (mask_auto; inclus tout ce qui peut être zéro/vides)
    mask_zero_honoraires = (df["Montant honoraires (US $)"] == 0)
    mask_acompte_positif = (df["Acompte 1"] > 0)
    mask_auto = mask_zero_honoraires & mask_acompte_positif

    # Union
    escrow_df = df[mask_escrow | mask_auto].copy()

    if escrow_df.empty:
        st.info("Aucun dossier en Escrow pour le moment.")
        return

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
