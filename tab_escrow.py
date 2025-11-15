import streamlit as st
import pandas as pd


def _to_bool(v):
    """Convertit toutes les valeurs Excel possibles en booléen."""
    if isinstance(v, bool):
        return v
    if pd.isna(v):
        return False
    
    v = str(v).strip().lower()
    return v in ["true", "vrai", "1", "yes", "oui", "x", "✔", "✓"]


def _to_num(series):
    """Convertit série Excel en float propre, même avec espaces/virgules."""
    return (
        pd.to_numeric(
            series.astype(str)
                  .str.replace("\u00a0", "", regex=False)
                  .str.replace(" ", "", regex=False)
                  .str.replace(",", ".", regex=False),
            errors="coerce",
        ).fillna(0.0)
    )


def tab_escrow():
    st.header("🛡️ Escrow")

    if "data_xlsx" not in st.session_state or st.session_state["data_xlsx"] is None:
        st.warning("⚠️ Fichier non chargé.")
        return

    data = st.session_state["data_xlsx"]
    df = data.get("Clients")

    if df is None or df.empty:
        st.info("Feuille Clients vide.")
        return

    # --- Nettoyage ---
    df = df.copy()
    
    df["Escrow"] = df["Escrow"].apply(_to_bool)
    acompte = _to_num(df["Acompte 1"])
    honoraires = _to_num(df["Montant honoraires (US $)"])

    # --- Règles Escrow ---
    mask_checkbox = df["Escrow"] == True
    mask_auto = (acompte > 0) & (honoraires == 0)

    df_escrow = df[mask_checkbox | mask_auto].copy()

    if df_escrow.empty:
        st.info("Aucun dossier en Escrow pour le moment.")
        return

    st.subheader("Dossiers en Escrow")

    st.metric("Total en attente", f"{acompte[mask_checkbox | mask_auto].sum():,.2f} $")

    cols = [c for c in [
        "Dossier N",
        "Nom",
        "Categories",
        "Sous-categorie",
        "Visa",
        "Acompte 1",
        "Montant honoraires (US $)",
        "Escrow"
    ] if c in df.columns]

    st.dataframe(df_escrow[cols].reset_index(drop=True))
