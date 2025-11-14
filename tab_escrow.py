import streamlit as st
import pandas as pd


def _to_bool(v):
    """Convertit ce qui vient d'Excel en booléen réel."""
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, float)):
        return v == 1
    if isinstance(v, str):
        return v.strip().lower() in ["true", "vrai", "1", "yes", "oui", "x"]
    return False


def _to_num(series):
    """Convertit une série Excel (avec virgules, espaces, etc.) en float propre."""
    return (
        pd.to_numeric(
            series.astype(str)
                  .str.replace("\u00a0", "", regex=False)  # espace insécable
                  .str.replace(" ", "", regex=False)      # espaces
                  .str.replace(",", ".", regex=False),    # virgule -> point
            errors="coerce",
        )
        .fillna(0.0)
    )


def tab_escrow():
    st.header("🛡️ Escrow")

    # --- vérif données ---
    if "data_xlsx" not in st.session_state or st.session_state["data_xlsx"] is None:
        st.warning("Fichier non chargé — veuillez l'importer via l’onglet 📄 Fichiers.")
        return

    data = st.session_state["data_xlsx"]
    df_clients = data.get("Clients")

    if df_clients is None:
        st.error("La feuille 'Clients' est manquante dans le fichier Excel.")
        return

    # --- normalisation colonnes nécessaires ---
    for col in ["Escrow", "Acompte 1", "Montant honoraires (US $)"]:
        if col not in df_clients.columns:
            st.error(f"La colonne '{col}' est absente de la feuille Clients.")
            return

    # Escrow -> booléen
    df_clients = df_clients.copy()
    df_clients["Escrow"] = df_clients["Escrow"].apply(_to_bool)

    # Nombres nettoyés
    acompte1 = _to_num(df_clients["Acompte 1"])
    honoraires = _to_num(df_clients["Montant honoraires (US $)"])

    # --- filtre Escrow ---
    mask_auto = (acompte1 > 0) & (honoraires == 0)
    mask_flag = df_clients["Escrow"] == True

    df_escrow = df_clients[mask_flag | mask_auto].copy()

    if df_escrow.empty:
        st.info("Aucun dossier en Escrow pour le moment.")
        return

    # --- affichage KPI + tableau ---
    st.subheader("Dossiers en Escrow")

    montant_total = _to_num(df_escrow["Acompte 1"]).sum()
    st.metric("Montant total", f"{montant_total:,.2f} $")

    # colonnes affichées (si elles existent)
    cols_aff = [
        "Dossier N",
        "Nom",
        "Categories",
        "Sous-categorie",
        "Visa",
        "Acompte 1",
        "Montant honoraires (US $)",
        "Escrow",
    ]
    cols_aff = [c for c in cols_aff if c in df_escrow.columns]

    st.dataframe(df_escrow[cols_aff].reset_index(drop=True))
