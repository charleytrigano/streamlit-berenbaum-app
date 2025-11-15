import streamlit as st
import pandas as pd
from common_data import ensure_loaded


def _to_bool(value):
    if isinstance(value, bool):
        return value
    s = str(value).strip().lower()
    return s in ("1", "true", "vrai", "oui", "yes", "x")


def tab_escrow():
    st.header("🛡️ Escrow")

    data = ensure_loaded()
    if data is None:
        st.warning("Aucune donnée chargée. Importe le fichier via 📄 Fichiers.")
        return

    df = data["Clients"].copy()
    if df.empty:
        st.info("Aucun dossier dans la feuille Clients.")
        return

    # Colonnes numériques utiles
    hono = pd.to_numeric(df["Montant honoraires (US $)"], errors="coerce").fillna(0.0)
    ac1 = pd.to_numeric(df["Acompte 1"], errors="coerce").fillna(0.0)

    # Escrow manuel (case cochée)
    escrow_manual = df["Escrow"].apply(_to_bool)

    # Escrow automatique : Acompte 1 > 0 et honoraires == 0
    escrow_auto = (ac1 > 0) & (hono == 0)

    escrow_mask = escrow_manual | escrow_auto
    df_escrow = df[escrow_mask].copy()

    if df_escrow.empty:
        st.info("Aucun dossier en Escrow pour le moment.")
        return

    # KPI
    nb_dossiers = len(df_escrow)
    total_acompte = ac1[escrow_mask].sum()

    c1, c2 = st.columns(2)
    with c1:
        st.metric("Nombre de dossiers en Escrow", nb_dossiers)
    with c2:
        st.metric("Total Acompte 1 (Escrow)", f"{total_acompte:,.2f} $")

    # Tableau des dossiers en Escrow
    cols_aff = [
        "Dossier N",
        "Nom",
        "Date",
        "Catégories",
        "Sous-catégories",
        "Visa",
        "Montant honoraires (US $)",
        "Acompte 1",
        "Date Acompte 1",
        "mode de paiement",
        "Escrow",
        "Dossier envoyé",
        "Date envoi",
        "Dossier accepté",
        "Dossier refusé",
        "Dossier Annulé",
        "RFE",
    ]
    cols_exist = [c for c in cols_aff if c in df_escrow.columns]

    st.markdown("### Liste des dossiers en Escrow")
    st.dataframe(
        df_escrow[cols_exist].style.format(
            {
                "Montant honoraires (US $)": "{:,.2f}",
                "Acompte 1": "{:,.2f}",
            }
        ),
        use_container_width=True,
    )
