import streamlit as st
import pandas as pd
from common_data import ensure_loaded, save_all, MAIN_FILE


def tab_escrow():
    st.header("🛡️ Escrow")

    data = ensure_loaded(MAIN_FILE)
    if data is None:
        st.warning("Aucun fichier chargé.")
        return

    df = data["Clients"].copy()

    # ---------------------------
    # NORMALISATION DES VALEURS
    # ---------------------------
    def to_bool(x):
        if str(x).strip().lower() in ["1", "true", "yes", "oui"]:
            return True
        return False

    df["Escrow_flag"] = df["Escrow"].apply(to_bool)

    # S’assurer que Acompte 1 est numérique
    df["Acompte 1"] = pd.to_numeric(df["Acompte 1"], errors="coerce").fillna(0)

    # S’assurer que Montant honoraires est numérique
    df["Montant honoraires (US $)"] = pd.to_numeric(
        df["Montant honoraires (US $)"], errors="coerce"
    ).fillna(0)

    # ---------------------------
    # RÈGLE DE SÉLECTION ESCROW
    # ---------------------------
    df_escrow = df[
        (df["Escrow_flag"] == True)
        | ((df["Acompte 1"] > 0) & (df["Montant honoraires (US $)"] == 0))
    ].copy()

    # Aucun dossier
    if df_escrow.empty:
        st.info("Aucun dossier en Escrow pour le moment.")
        return

    # ---------------------------
    # AFFICHAGE LISTE ESCROW
    # ---------------------------
    st.subheader("📋 Dossiers en Escrow")

    display_cols = [
        "Dossier N",
        "Nom",
        "Acompte 1",
        "Date Acompte 1",
        "Montant honoraires (US $)",
        "Escrow",
    ]

    # Formatage des dates
    for c in ["Date Acompte 1"]:
        df_escrow[c] = pd.to_datetime(df_escrow[c], errors="coerce").dt.date

    st.dataframe(df_escrow[display_cols])

    # ---------------------------
    # SECTION : DOSSIER RECLAMÉ
    # ---------------------------
    st.subheader("📤 Marquer un dossier comme réclamé")

    choix = st.selectbox(
        "Sélectionner un dossier",
        df_escrow["Dossier N"].astype(str).tolist(),
        index=None,
        placeholder="Choisir un dossier en Escrow",
    )

    if choix:
        dossier_id = int(choix)

        date_reclame = st.date_input("Date de réclamation", pd.Timestamp.today().date())

        if st.button("📨 Marquer comme réclamé"):
            idx = df.index[df["Dossier N"] == dossier_id][0]
            df.loc[idx, "Dossier envoye"] = pd.to_datetime(date_reclame).date()

            data["Clients"] = df
            save_all()

            st.success(f"Dossier {dossier_id} marqué comme réclamé.")
            st.rerun()
