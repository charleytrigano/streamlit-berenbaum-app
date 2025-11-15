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
    # Convertir en float propre
    def to_float(x):
        try:
            return float(str(x).replace(",", ".").replace(" ", ""))
        except:
            return 0.0

    df["Acompte 1"] = df["Acompte 1"].apply(to_float)
    df["Acompte 2"] = df["Acompte 2"].apply(to_float)
    df["Acompte 3"] = df["Acompte 3"].apply(to_float)
    df["Acompte 4"] = df["Acompte 4"].apply(to_float)
    df["Montant honoraires (US $)"] = df["Montant honoraires (US $)"].apply(to_float)

    # --- Conditions Escrow ---
    acompte_condition = (
        (df["Acompte 1"] > 0)
        | (df["Acompte 2"] > 0)
        | (df["Acompte 3"] > 0)
        | (df["Acompte 4"] > 0)
    )

    honoraires_zero = df["Montant honoraires (US $)"] == 0

    escrow_auto = acompte_condition & honoraires_zero

    # --- Résultat final ---
    escrow_df = df[(df["Escrow"] == True) | (escrow_auto)]

    if escrow_df.empty:
        st.info("Aucun dossier en Escrow pour le moment.")
        return

    st.subheader("📋 Dossiers détectés en Escrow")
    st.dataframe(
        escrow_df[
            [
                "Dossier N",
                "Nom",
                "Acompte 1",
                "Acompte 2",
                "Acompte 3",
                "Acompte 4",
                "Montant honoraires (US $)",
                "Escrow",
            ]
        ],
        use_container_width=True
    )
