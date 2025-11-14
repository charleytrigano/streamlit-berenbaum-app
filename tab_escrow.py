import streamlit as st
import pandas as pd
from datetime import date
from common_data import ensure_loaded, save_all, MAIN_FILE


# Colonnes attendues dans la feuille Escrow
ESCROW_COLS = [
    "Dossier N",
    "Nom",
    "Montant",
    "Date envoi",
    "Etat",
    "Date reclamation",
]


def _ensure_escrow_sheet(data: dict) -> pd.DataFrame:
    """S'assure que la feuille Escrow existe et contient au moins les colonnes nécessaires."""
    if "Escrow" not in data or not isinstance(data["Escrow"], pd.DataFrame):
        df_esc = pd.DataFrame(columns=ESCROW_COLS)
        data["Escrow"] = df_esc
        return df_esc

    df_esc = data["Escrow"].copy()

    # Ajout des colonnes manquantes
    for col in ESCROW_COLS:
        if col not in df_esc.columns:
            df_esc[col] = pd.NA

    # On garde toutes les colonnes existantes mais on s'assure que celles qu'on utilise sont présentes
    data["Escrow"] = df_esc
    return df_esc


def _auto_fill_from_clients(df_clients: pd.DataFrame, df_escrow: pd.DataFrame) -> pd.DataFrame:
    """
    Ajoute automatiquement dans Escrow les dossiers qui ont :
      - Acompte 1 > 0
      - Montant honoraires (US $) == 0
    sans dupliquer ceux déjà présents.
    """
    if df_clients.empty:
        return df_escrow

    acompte1 = pd.to_numeric(df_clients.get("Acompte 1", 0), errors="coerce").fillna(0)
    honoraires = pd.to_numeric(df_clients.get("Montant honoraires (US $)", 0), errors="coerce").fillna(0)

    mask = (acompte1 > 0) & (honoraires == 0)
    auto_df = df_clients[mask].copy()
    if auto_df.empty:
        return df_escrow

    # Dossiers déjà en Escrow
    existing_ids = set(df_escrow["Dossier N"].astype(str).dropna().tolist())

    rows_to_add = []
    for _, row in auto_df.iterrows():
        did = str(row.get("Dossier N", "")).strip()
        if not did or did in existing_ids:
            continue

        montant_val = pd.to_numeric(row.get("Acompte 1", 0), errors="coerce")
        if pd.isna(montant_val):
            montant_val = 0.0

        rows_to_add.append(
            {
                "Dossier N": row.get("Dossier N", ""),
                "Nom": row.get("Nom", ""),
                "Montant": float(montant_val),
                "Date envoi": pd.NaT,
                "Etat": "",
                "Date reclamation": pd.NaT,
            }
        )

    if rows_to_add:
        df_add = pd.DataFrame(rows_to_add, columns=ESCROW_COLS)
        df_escrow = pd.concat([df_escrow, df_add], ignore_index=True)

    return df_escrow


def _format_dates_for_display(df: pd.DataFrame, cols) -> pd.DataFrame:
    """Formate les dates en AAAA-MM-JJ (sans heure) pour l'affichage."""
    df = df.copy()
    for c in cols:
        if c in df.columns:
            df[c] = (
                pd.to_datetime(df[c], errors="coerce")
                .dt.strftime("%Y-%m-%d")
                .fillna("")
            )
    return df


def _format_amount(value: float) -> str:
    """Format numérique : ### ###.## $"""
    try:
        v = float(value)
    except Exception:
        v = 0.0
    txt = f"{v:,.2f} $"
    # remplace les séparateurs en style FR : espace pour milliers, virgule pour décimales
    txt = txt.replace(",", "X").replace(".", ",").replace("X", " ")
    return txt


def tab_escrow():
    st.header("🛡️ Escrow")

    data = ensure_loaded(MAIN_FILE)
    if data is None:
        st.warning("⚠️ Aucune donnée. Importe le fichier via l’onglet 📂 Fichiers.")
        return

    df_clients = data.get("Clients", pd.DataFrame())
    df_escrow = _ensure_escrow_sheet(data)

    # ------------------------------------------------------------------
    # 1) Compléter automatiquement Escrow à partir des dossiers Clients
    # ------------------------------------------------------------------
    df_escrow_before = df_escrow.copy()
    df_escrow = _auto_fill_from_clients(df_clients, df_escrow)

    # Si on a ajouté des lignes, on sauvegarde
    if len(df_escrow) != len(df_escrow_before):
        data["Escrow"] = df_escrow
        save_all()

    # ------------------------------------------------------------------
    # 2) KPI : nombre de dossiers + montant total
    # ------------------------------------------------------------------
    montant_total = pd.to_numeric(df_escrow.get("Montant", 0), errors="coerce").fillna(0).sum()
    nb_dossiers = len(df_escrow)

    col_k1, col_k2 = st.columns(2)
    with col_k1:
        st.metric("Nombre de dossiers en Escrow", nb_dossiers)
    with col_k2:
        st.metric("Montant total en Escrow", _format_amount(montant_total))

    st.markdown("---")

    # ------------------------------------------------------------------
    # 3) Tables : Tous / À réclamer / Réclamés
    # ------------------------------------------------------------------
    if df_escrow.empty:
        st.info("Aucun dossier en Escrow pour le moment.")
        return

    # Pour l'affichage : dates format AAAA-MM-JJ
    display_df = _format_dates_for_display(df_escrow, ["Date envoi", "Date reclamation"])

    # Tous les dossiers
    st.subheader("📋 Tous les dossiers en Escrow")
    st.dataframe(display_df[ESCROW_COLS], use_container_width=True)

    # À réclamer : Date envoi renseignée ET Date reclamation vide
    df_a_reclamer = display_df[
        (display_df["Date envoi"] != "") & (display_df["Date reclamation"] == "")
    ]

    st.subheader("📮 Dossiers envoyés – à réclamer")
    if df_a_reclamer.empty:
        st.info("Aucun dossier à réclamer.")
    else:
        st.dataframe(df_a_reclamer[ESCROW_COLS], use_container_width=True)

    # Réclamés : Date reclamation renseignée
    df_reclames = display_df[display_df["Date reclamation"] != ""]

    st.subheader("✅ Dossiers réclamés")
    if df_reclames.empty:
        st.info("Aucun dossier marqué comme réclamé.")
    else:
        st.dataframe(df_reclames[ESCROW_COLS], use_container_width=True)

    st.markdown("---")

    # ------------------------------------------------------------------
    # 4) Marquer un dossier comme réclamé
    # ------------------------------------------------------------------
    st.subheader("🖊️ Marquer un dossier comme réclamé")

    col1, col2 = st.columns([1, 1])
    with col1:
        num = st.text_input("Numéro de dossier à marquer comme réclamé")
    with col2:
        date_rec = st.date_input("Date de réclamation", value=date.today())

    if st.button("📌 Marquer comme réclamé"):
        num = (num or "").strip()
        if not num:
            st.warning("Merci de saisir un numéro de dossier.")
            return

        mask = df_escrow["Dossier N"].astype(str) == num
        if not mask.any():
            st.warning("Numéro de dossier introuvable dans Escrow.")
            return

        # Mise à jour de l'état + date
        df_escrow.loc[mask, "Etat"] = "Réclamé"
        df_escrow.loc[mask, "Date reclamation"] = pd.to_datetime(date_rec)

        # Sauvegarde
        data["Escrow"] = df_escrow
        save_all()

        st.success(f"Dossier {num} marqué comme réclamé.")
