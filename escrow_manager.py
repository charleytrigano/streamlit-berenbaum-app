import streamlit as st
import pandas as pd
from common_data import ensure_loaded, save_all, MAIN_FILE


def tab_escrow():
    st.header("🛡️ Escrow")

    data = ensure_loaded(MAIN_FILE)
    if data is None:
        st.warning("Aucun fichier chargé.")
        return

    df = data["Clients"]

    # Normalisation des valeurs Escrow (True / 1 / oui…)
    df["Escrow"] = df["Escrow"].astype(str).str.lower().isin(["1", "true", "oui", "yes", "y"])

    # Conditions Escrow auto
    escrow_auto = (df["Acompte 1"].fillna(0) > 0) & (df["Montant honoraires (US $)"].fillna(0) == 0)

    # Dossiers réellement Escrow
    df_escrow = df[df["Escrow"] | escrow_auto].copy()

    # Dossiers envoyés = avec case cochée "Dossier envoyé"
    df_envoyes = df_escrow[df_escrow["Dossier envoyé"].astype(str).str.lower().isin(["1", "true", "oui", "yes"])].copy()

    # Dossiers non envoyés = Escrow mais "Dossier envoyé" non cochée
    df_a_envoyer = df_escrow[~df_escrow.index.isin(df_envoyes.index)].copy()

    st.subheader("📌 Dossiers en Escrow (à envoyer)")

    if df_a_envoyer.empty:
        st.info("Aucun dossier en Escrow pour le moment.")
    else:
        st.dataframe(df_a_envoyer[
            ["Dossier N", "Nom", "Acompte 1", "Montant honoraires (US $)", "Escrow"]
        ])

    st.markdown("---")
    st.subheader("📤 Dossiers envoyés (Escrow à réclamer)")

    if df_envoyes.empty:
        st.info("Aucun dossier Escrow envoyé pour le moment.")
    else:
        st.dataframe(df_envoyes[
            ["Dossier N", "Nom", "Date envoi", "Acompte 1", "Montant honoraires (US $)"]
        ])

    st.markdown("---")
    st.subheader("✏️ Enregistrer l'envoi d’un dossier")

    ids = df_escrow["Dossier N"].tolist()
    if not ids:
        st.info("Aucun dossier sélectionnable.")
        return

    selected = st.selectbox("Choisir un dossier à marquer comme envoyé :", ids)

    send = st.checkbox("Dossier envoyé ?")
    date_send = st.date_input("Date envoi")

    if st.button("💾 Enregistrer l'envoi"):
        idx = df[df["Dossier N"] == selected].index[0]
        df.loc[idx, "Dossier envoyé"] = send
        df.loc[idx, "Date envoi"] = pd.to_datetime(date_send)

        save_all()
        st.success("Dossier mis à jour !")
