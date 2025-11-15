import streamlit as st
import pandas as pd
from common_data import ensure_loaded, save_all, MAIN_FILE


def _to_float(s):
    try:
        return float(str(s).replace(" ", "").replace(",", "."))
    except Exception:
        return 0.0


def tab_escrow():
    st.header("🛡️ Escrow")

    data = ensure_loaded(MAIN_FILE)
    if data is None:
        return

    df = data.get("Clients", pd.DataFrame()).copy()
    if df.empty:
        st.info("Aucun dossier client disponible.")
        return

    # S'assurer que toutes les colonnes existent
    for col in [
        "Dossier N",
        "Nom",
        "Escrow",
        "Acompte 1",
        "Montant honoraires (US $)",
        "Dossier envoyé",
        "Date envoi",
    ]:
        if col not in df.columns:
            df[col] = pd.NA

    # Numériques propres
    df["Acompte 1"] = df["Acompte 1"].map(_to_float)
    df["Montant honoraires (US $)"] = df["Montant honoraires (US $)"].map(_to_float)

    # Normalisation Escrow -> bool
    def _to_bool(x):
        if isinstance(x, bool):
            return x
        s = str(x).strip().lower()
        return s in {"1", "x", "oui", "true", "vrai"}

    df["Escrow"] = df["Escrow"].apply(_to_bool)

    # Règle automatique : Acompte 1 > 0 et Montant honoraires = 0 => Escrow = True
    auto_mask = (df["Acompte 1"] > 0) & (df["Montant honoraires (US $)"] == 0)
    df.loc[auto_mask, "Escrow"] = True

    # Séparation A RECLAMER / RECLAMES
    df_escrow = df[df["Escrow"] == True].copy()

    def _sent_bool(x):
        if isinstance(x, bool):
            return x
        s = str(x).strip().lower()
        return s in {"1", "x", "oui", "true", "vrai"}

    df_escrow["Dossier envoyé"] = df_escrow["Dossier envoyé"].apply(_sent_bool)

    a_reclamer = df_escrow[df_escrow["Dossier envoyé"] != True].copy()
    reclames = df_escrow[df_escrow["Dossier envoyé"] == True].copy()

    # KPIs
    total_montant = df_escrow["Acompte 1"].sum()
    nb_dossiers = len(df_escrow)

    c1, c2 = st.columns(2)
    with c1:
        st.metric("Nombre de dossiers en Escrow", nb_dossiers)
    with c2:
        st.metric("Montant total en Escrow", f"{total_montant:,.2f} $")

    # LISTE A RECLAMER
    st.subheader("📌 Dossiers en Escrow à réclamer")
    if a_reclamer.empty:
        st.info("Aucun dossier à réclamer pour le moment.")
    else:
        cols = ["Dossier N", "Nom", "Acompte 1"]
        for c in cols:
            if c not in a_reclamer.columns:
                a_reclamer[c] = ""
        st.dataframe(
            a_reclamer[cols].sort_values("Dossier N"),
            use_container_width=True,
        )

    st.markdown("---")

    # Marquer comme "Dossier envoyé"
    st.subheader("✉️ Marquer un dossier comme envoyé")
    col_num, col_date, col_btn = st.columns([1, 1, 1])

    with col_num:
        num_envoye = st.text_input("Dossier N", key="escrow_num_envoye")

    with col_date:
        date_envoi = st.date_input("Date envoi", key="escrow_date_envoi")

    with col_btn:
        if st.button("✅ Valider l'envoi", key="escrow_btn_envoye"):
            if num_envoye.strip():
                mask = df["Dossier N"].astype(str) == num_envoye.strip()
                if mask.any():
                    idx = df[mask].index[0]
                    df.at[idx, "Dossier envoyé"] = True
                    df.at[idx, "Date envoi"] = pd.to_datetime(date_envoi)
                    # on replace dans data_xlsx et on sauvegarde
                    data["Clients"] = df
                    st.session_state["data_xlsx"] = data
                    save_all()
                    st.success(f"Dossier {num_envoye} marqué comme envoyé.")
                else:
                    st.warning("Dossier introuvable.")
            else:
                st.warning("Merci de saisir un numéro de dossier.")

    st.markdown("---")

    # LISTE RECLAMES
    st.subheader("📬 Dossiers Escrow réclamés (envoyés)")
    if reclames.empty:
        st.info("Aucun dossier Escrow réclamé pour le moment.")
    else:
        cols_r = ["Dossier N", "Nom", "Acompte 1", "Date envoi"]
        for c in cols_r:
            if c not in reclames.columns:
                reclames[c] = ""
        # Date envoi joli format
        if "Date envoi" in reclames.columns:
            reclames["Date envoi"] = pd.to_datetime(
                reclames["Date envoi"], errors="coerce"
            ).dt.strftime("%Y-%m-%d")
        st.dataframe(
            reclames[cols_r].sort_values("Dossier N"),
            use_container_width=True,
        )
