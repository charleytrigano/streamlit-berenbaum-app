import streamlit as st
import pandas as pd

from common_data import ensure_loaded, MAIN_FILE


def _to_float(s: pd.Series) -> pd.Series:
    """Convertit en float, NaN -> 0."""
    return pd.to_numeric(s, errors="coerce").fillna(0.0)


def _is_truthy(v) -> bool:
    """Interprète 1 / x / true / oui / date non vide comme True."""
    if pd.isna(v):
        return False
    if isinstance(v, (int, float)) and v != 0:
        return True
    s = str(v).strip().lower()
    if not s:
        return False
    # valeur textuelle
    if s in {"1", "true", "vrai", "oui", "y", "x"}:
        return True
    # une date écrite (ex: 2024-10-01) → True
    return True if any(c.isdigit() for c in s) and "-" in s else False


def _fmt_amount(v) -> str:
    """Format 12345.6 -> 12 345.60 $"""
    try:
        v = float(v)
    except Exception:
        return ""
    s = f"{v:,.2f}"          # 12,345.60
    s = s.replace(",", " ")  # 12 345.60
    return s + " $"


def _fmt_date_col(series: pd.Series) -> pd.Series:
    """Convertit en texte AAAA-MM-JJ, vide si NaT."""
    dt = pd.to_datetime(series, errors="coerce")
    return dt.dt.strftime("%Y-%m-%d").fillna("")


def tab_escrow():
    st.header("🛡️ Escrow")

    data = ensure_loaded(MAIN_FILE)
    if data is None:
        st.warning("Fichier non chargé — importe d’abord ton Excel via l’onglet **📄 Fichiers**.")
        return

    # --- Feuilles de base ---
    df_clients = data.get("Clients", pd.DataFrame())
    df_escrow_sheet = data.get("Escrow", pd.DataFrame())

    if df_clients.empty:
        st.info("La feuille **Clients** est vide. Aucun dossier en Escrow.")
        return

    # Sécurité : s'assurer que les colonnes de base existent
    for col in [
        "Dossier N",
        "Nom",
        "Montant honoraires (US $)",
        "Acompte 1",
        "Escrow",
        "Dossier envoye",
        "Dossier accepte",
        "Dossier refuse",
        "Dossier annule",
        "RFE",
        "Date RFE",
    ]:
        if col not in df_clients.columns:
            df_clients[col] = pd.NA

    # --- Normalisation des montants ---
    honoraires = _to_float(df_clients["Montant honoraires (US $)"])
    acompte1 = _to_float(df_clients["Acompte 1"])

    # --- Colonne Escrow "cochée" (1, x, oui, date, etc.) ---
    esc_col = df_clients["Escrow"]
    esc_checked = esc_col.map(_is_truthy)

    # --- Condition automatique : Acompte 1 > 0 et honoraires == 0 ---
    esc_auto = (acompte1 > 0) & (honoraires == 0)

    mask_escrow = esc_checked | esc_auto
    df_candidates = df_clients[mask_escrow].copy()

    if df_candidates.empty:
        st.success("Aucun dossier en Escrow actuellement. 🎉")
        return

    # --- Normalisation des IDs pour pouvoir joindre avec la feuille Escrow ---
    def _norm_id(s: pd.Series) -> pd.Series:
        return pd.to_numeric(s, errors="coerce").astype("Int64")

    df_candidates["_id_"] = _norm_id(df_candidates["Dossier N"])

    if not df_escrow_sheet.empty:
        # On s'assure que les colonnes existent
        for col in ["Dossier N", "Montant", "Date envoi", "Etat", "Date reclamation"]:
            if col not in df_escrow_sheet.columns:
                df_escrow_sheet[col] = pd.NA

        df_escrow_sheet = df_escrow_sheet.copy()
        df_escrow_sheet["_id_"] = _norm_id(df_escrow_sheet["Dossier N"])

        df_esc_merge = df_escrow_sheet[["_id_", "Montant", "Date envoi", "Etat", "Date reclamation"]]
    else:
        df_esc_merge = pd.DataFrame(columns=["_id_", "Montant", "Date envoi", "Etat", "Date reclamation"])

    merged = pd.merge(
        df_candidates,
        df_esc_merge,
        on="_id_",
        how="left",
        suffixes=("", "_esc")
    )

    # --- Montant Escrow = Montant de la feuille Escrow, sinon Acompte 1 ---
    merged["Montant_Escrow"] = _to_float(merged.get("Montant", pd.Series(dtype=float)))
    mask_empty_montant = merged["Montant_Escrow"] == 0
    merged.loc[mask_empty_montant, "Montant_Escrow"] = acompte1.loc[merged.index][mask_empty_montant]

    total_montant = float(merged["Montant_Escrow"].sum())

    # ===================== KPIs =====================
    k1, k2 = st.columns(2)
    k1.metric("Nombre de dossiers en Escrow", int(len(merged)))
    k2.metric("Montant total en Escrow", _fmt_amount(total_montant))

    st.markdown("---")

    # ===================== TABLEAU PRINCIPAL =====================
    st.subheader("📋 Dossiers en Escrow")

    df_display = merged[[
        "Dossier N",
        "Nom",
        "Montant_Escrow",
        "Date envoi",
        "Etat",
        "Date reclamation",
        "Dossier envoye",
        "Dossier accepte",
        "Dossier refuse",
        "Dossier annule",
        "RFE",
    ]].copy()

    df_display.rename(columns={
        "Montant_Escrow": "Montant Escrow",
        "Date envoi": "Date envoi (Escrow)",
        "Date reclamation": "Date réclamation (Escrow)",
    }, inplace=True)

    # Formatage des dates
    df_display["Date envoi (Escrow)"] = _fmt_date_col(df_display["Date envoi (Escrow)"])
    df_display["Date réclamation (Escrow)"] = _fmt_date_col(df_display["Date réclamation (Escrow)"])

    st.dataframe(
        df_display.style.format({"Montant Escrow": _fmt_amount}),
        use_container_width=True
    )

    # ===================== ESCROW À RÉCLAMER =====================
    st.markdown("---")
    st.subheader("📨 Escrow à réclamer")

    # Dossier envoyé = date ou champ non vide
    sent = merged["Dossier envoye"].map(_is_truthy) | merged["Date envoi"].map(_is_truthy)

    accepted = merged["Dossier accepte"].map(_is_truthy)
    refused = merged["Dossier refuse"].map(_is_truthy)
    cancelled = merged["Dossier annule"].map(_is_truthy)
    rfe = merged["RFE"].map(_is_truthy)

    to_reclaim_mask = sent & ~(accepted | refused | cancelled | rfe)
    df_to_reclaim = merged[to_reclaim_mask].copy()

    if df_to_reclaim.empty:
        st.info("Aucun dossier à réclamer pour le moment.")
    else:
        df_to_reclaim_view = df_to_reclaim[[
            "Dossier N",
            "Nom",
            "Montant_Escrow",
            "Date envoi",
        ]].copy()
        df_to_reclaim_view.rename(columns={
            "Montant_Escrow": "Montant Escrow",
            "Date envoi": "Date envoi (Escrow)",
        }, inplace=True)
        df_to_reclaim_view["Date envoi (Escrow)"] = _fmt_date_col(df_to_reclaim_view["Date envoi (Escrow)"])

        st.dataframe(
            df_to_reclaim_view.style.format({"Montant Escrow": _fmt_amount}),
            use_container_width=True
        )

    # ===================== ESCROW RÉCLAMÉS / CLOS =====================
    st.markdown("---")
    st.subheader("✅ Escrow réclamés / clôturés")

    closed_mask = accepted | refused | cancelled | rfe
    df_closed = merged[closed_mask].copy()

    if df_closed.empty:
        st.info("Aucun dossier Escrow encore clôturé.")
    else:
        df_closed_view = df_closed[[
            "Dossier N",
            "Nom",
            "Montant_Escrow",
            "Etat",
            "Date reclamation",
            "Dossier accepte",
            "Dossier refuse",
            "Dossier annule",
            "RFE",
        ]].copy()

        df_closed_view.rename(columns={
            "Montant_Escrow": "Montant Escrow",
            "Date reclamation": "Date réclamation (Escrow)",
        }, inplace=True)
        df_closed_view["Date réclamation (Escrow)"] = _fmt_date_col(df_closed_view["Date réclamation (Escrow)"])

        st.dataframe(
            df_closed_view.style.format({"Montant Escrow": _fmt_amount}),
            use_container_width=True
        )
