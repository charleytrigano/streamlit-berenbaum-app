import streamlit as st
import pandas as pd
from common_data import ensure_loaded, MAIN_FILE


def _to_bool(v):
    """Convertit ce qui vient d'Excel en bool."""
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, float)):
        return v == 1
    if isinstance(v, str):
        return v.strip().lower() in ["true", "vrai", "1", "yes", "oui", "x"]
    return False


def _to_num(series):
    """Convertit une série (texte, virgules, espaces) en float propre."""
    return (
        pd.to_numeric(
            series.astype(str)
            .str.replace("\u00A0", "", regex=False)
            .str.replace(" ", "", regex=False)
            .str.replace(",", ".", regex=False),
            errors="coerce",
        )
        .fillna(0.0)
    )


def tab_escrow():
    st.header("🛡️ Escrow")

    data = ensure_loaded(MAIN_FILE)
    if data is None:
        st.warning("Fichier non chargé — importer via l’onglet 📄 Fichiers.")
        return

    df = data.get("Clients")
    if df is None or df.empty:
        st.info("Aucun dossier dans la feuille Clients.")
        return

    # vérif colonnes minimales
    for col in ["Escrow", "Acompte 1", "Montant honoraires (US $)"]:
        if col not in df.columns:
            st.error(f"Colonne manquante dans Clients : '{col}'")
            return

    df = df.copy()

    # normalisation
    df["Escrow"] = df["Escrow"].apply(_to_bool)
    acompte1 = _to_num(df["Acompte 1"])
    honoraires = _to_num(df["Montant honoraires (US $)"])

    # règle métier
    mask_flag = df["Escrow"] == True
    mask_auto = (acompte1 > 0) & (honoraires == 0)

    df_escrow = df[mask_flag | mask_auto].copy()

    if df_escrow.empty:
        st.info("Aucun dossier en Escrow pour le moment.")
        return

    # KPI
    montant_total = acompte1[mask_flag | mask_auto].sum()
    st.metric("Montant total Acompte 1 en Escrow", f"{montant_total:,.2f} $")

    # colonnes affichées si elles existent
    cols_aff = [
        "Dossier N",
        "Nom",
        "Catégories",
        "Sous-catégories",
        "Visa",
        "Acompte 1",
        "Montant honoraires (US $)",
        "Escrow",
    ]
    cols_aff = [c for c in cols_aff if c in df_escrow.columns]

    st.dataframe(df_escrow[cols_aff].reset_index(drop=True), use_container_width=True)
