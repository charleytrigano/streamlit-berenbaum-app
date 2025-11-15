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

    # -- DIAGNOSTIC Visualisation de la table brute --
    st.subheader("Vue brute des données clients (pour diagnostics)")
    st.write(df.head(20))

    # Nettoyage des colonnes concernées
    def to_float(x):
        try:
            return float(str(x).replace(",", ".").replace(" ", ""))
        except Exception:
            return 0.0

    df["Montant honoraires (US $)"] = df["Montant honoraires (US $)"].apply(to_float)
    df["Acompte 1"] = df["Acompte 1"].apply(to_float)
    if "Escrow" not in df.columns:
        df["Escrow"] = False

    # Nettoyage Escrow : bool robuste
    def escrow_bool(val):
        val = str(val).strip().lower()
        return val in ["true", "vrai", "1", "oui", "o", "ok", "x"]

    df["Escrow"] = df["Escrow"].apply(escrow_bool)

    # -- Affichage diagnostic des valeurs utiles --
    st.write("Résumé des valeurs 'Montant honoraires (US $)' et 'Acompte 1' :", df[["Montant honoraires (US $)", "Acompte 1", "Escrow"]].head(20))

    # Filtre 1 : Escrow coché (case, boutons…)
    mask_escrow = df["Escrow"]
    # Filtre 2 : Honoraires à 0 et acompte 1 > 0
    mask_auto = (df["Montant honoraires (US $)"] == 0) & (df["Acompte 1"] > 0)
    # Union
    escrow_df = df[mask_escrow | mask_auto].copy()

    # -- Affichage diagnostic de la table filtrée --
    st.write("Dossiers sélectionnés en ESCROW :", escrow_df.head(20))

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
