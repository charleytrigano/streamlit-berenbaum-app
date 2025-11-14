import streamlit as st
import pandas as pd
from common_data import ensure_loaded, save_all, MAIN_FILE


def tab_ajouter():
    st.header("➕ Ajouter un dossier")

    data = ensure_loaded(MAIN_FILE)
    if data is None:
        st.warning("Aucun fichier chargé.")
        return

    df = data["Clients"]

    # --- ID AUTO Fiable ---
    # Conversion forcée en numérique, tout le reste devient NaN
    ids = pd.to_numeric(df["Dossier N"], errors="coerce")
    ids = ids.dropna()

    if ids.empty:
        next_id = 1
    else:
        next_id = int(ids.max()) + 1

    st.info(f"**Numéro de dossier attribué automatiquement : {next_id}**")
