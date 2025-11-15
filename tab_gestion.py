import streamlit as st
import pandas as pd
from common_data import ensure_loaded, save_all, MAIN_FILE


def _to_date(value, default=None):
    """Convertit ce qui vient d'Excel en date, ou renvoie default."""
    if value is None or str(value).strip() == "":
        return default
    try:
        return pd.to_datetime(value).date()
    except Exception:
        return default


def _to_float(value):
    """Convertit montants Excel (virgule, espaces, etc.) en float."""
    try:
        s = str(value).replace("\u00A0", "").replace(" ", "").replace(",", ".")
        return float(s) if s not in ("", "nan", "None") else 0.0
    except Exception:
        return 0.0


def tab_gestion():
    st.header("✏️ / 🗑️ Gestion d’un dossier")

    data = ensure_loaded(MAIN_FILE)
    if data is None:
        st.warning("Aucun fichier chargé.")
        return

    if "Clients" not in data:
        st.error("La feuille 'Clients' est absente.")
        return

    df = data["Clients"]

    if df.empty:
        st.warning("Aucun dossier dans la feuille Clients.")
        return

    # -------------------------
    # Sélection du dossier
    # -------------------------
    st.subheader("📁 Sélection du dossier")

    # liste des dossiers numériques possibles
    dossier_list = (
        pd.to_numeric(df["Dossier N"], errors="coerce")
        .dropna()
        .astype(str)
        .tolist()
    )
    if not dossier_list:
        st.warning("Aucun dossier valide.")
        return

    selected = st.selectbox("Choisir un Dossier N", dossier_list)
    # on récupère la ligne
    mask = df["Dossier N"].astype(str) == str(selected)
    if not mask.any():
        st.error("Dossier introuvable.")
        return

    dossier = df[mask].iloc[0]

    # helpers pour les noms de colonnes (tolérant aux anciennes variantes)
    def col_name(candidates, create_if_missing=None):
        for c in candidates:
            if c in df.columns:
                return c
        if create_if_missing:
            # on crée la colonne si elle n'existe pas, remplie de valeurs vides
            df[create_if_missing] = ""
            return create_if_missing
        return None

    col_cat = col_name(["Catégories", "Categories", "Categorie"], "Catégories")
    col_scat = col_name(
        ["Sous-catégories", "Sous-categories", "Sous-categorie"],
        "Sous-catégories",
    )
    col_mh = col_name(["Montant honoraires (US $)"], "Montant honoraires (US $)")
    col_af = col_name(["Autres frais (US $)"], "Autres frais (US $)")
    col_ac1 = col_name(["Acompte 1"], "Acompte 1")
    col_dt_ac1 = col_name(["Date Acompte 1"], "Date Acompte 1")
    col_mode = col_name(["mode de paiement", "Mode de paiement"], "mode de paiement")
    col_escrow = col_name(["Escrow"], "Escrow")
    col_d_env = col_name(["Dossier envoyé"], "Dossier envoyé")
    col_dt_env = col_name(["Date envoi"], "Date envoi")
    col_d_acc = col_name(["Dossier accepté"], "Dossier accepté")
    col_dt_acc = col_name(["Date acceptation"], "Date acceptation")
    col_d_ref = col_name(["Dossier refusé"], "Dossier refusé")
    col_dt_ref = col_name(["Date refus"], "Date refus")
    col_d_ann = col_name(["Dossier Annulé", "Dossier annulé"], "Dossier Annulé")
    col_dt_ann = col_name(["Date annulation"], "Date annulation")
    col_rfe = col_name(["RFE"], "RFE")
    col_com = col_name(["Commentaires"], "Commentaires")

    # -------------------------
    # SECTION 1 — Informations générales
    # -------------------------
    st.subheader("👤 Informations générales")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        dossier_n = st.text_input("Dossier N", str(dossier["Dossier N"]))
    with col2:
        nom = st.text_input("Nom", str(dossier["Nom"]))
    with col3:
        categorie = st.text_input(
            "Catégories", str(dossier.get(col_cat, "")) if col_cat else ""
        )
    with col4:
        sous_cat = st.text_input(
            "Sous-catégories", str(dossier.get(col_scat, "")) if col_scat else ""
        )

    col5, col6 = st.columns(2)
    with col5:
        visa = st.text_input("Visa", str(dossier.get("Visa", "")))
    with col6:
        date_creation = st.date_input(
            "Date du dossier",
            _to_date(dossier.get("Date"), default=pd.Timestamp.today().date()),
        )

    # -------------------------
    # SECTION 2 — Montants
    # -------------------------
    st.subheader("💰 Montants")

    colA, colB = st.columns(2)
    with colA:
        montant_hono = st.number_input(
            "Montant honoraires (US $)",
            min_value=0.0,
            value=_to_float(dossier.get(col_mh, 0.0)) if col_mh else 0.0,
            step=50.0,
        )
    with colB:
        autres_frais = st.number_input(
            "Autres frais (US $)",
            min_value=0.0,
            value=_to_float(dossier.get(col_af, 0.0)) if col_af else 0.0,
            step=10.0,
        )

    # -------------------------
    # SECTION 3 — Acompte 1
    # -------------------------
    st.subheader("💵 Acompte 1")

    c1, c2, c3 = st.columns(3)
    with c1:
        acompte1 = st.number_input(
            "Acompte 1",
            min_value=0.0,
            value=_to_float(dossier.get(col_ac1, 0.0)) if col_ac1 else 0.0,
            step=10.0,
        )
    with c2:
        date_acompte1 = st.date_input(
            "Date Acompte 1",
            _to_date(
                dossier.get(col_dt_ac1),
                default=pd.Timestamp.today().date(),
            )
            if col_dt_ac1
            else pd.Timestamp.today().date(),
        )
    with c3:
        mode_paiement = st.text_input(
            "Mode de paiement",
            str(dossier.get(col_mode, "")) if col_mode else "",
        )

    # -------------------------
    # SECTION 4 — Statut / Escrow / RFE
    # -------------------------
    st.subheader("📌 Statut du dossier & Escrow")

    c4, c5 = st.columns(2)
    with c4:
        escrow_checked = st.checkbox(
            "Escrow",
            value=bool(dossier.get(col_escrow, False)) if col_escrow else False,
        )
    with c5:
        rfe = st.checkbox("RFE", value=bool(dossier.get(col_rfe, False)) if col_rfe else False)

    s1, s2 = st.columns(2)
    with s1:
        dossier_envoye = st.checkbox(
            "Dossier envoyé",
            value=bool(dossier.get(col_d_env, False)) if col_d_env else False,
        )
    with s2:
        date_envoye = st.date_input(
            "Date envoi",
            _to_date(dossier.get(col_dt_env)) if col_dt_env else None,
        )

    s3, s4 = st.columns(2)
    with s3:
        dossier_accepte = st.checkbox(
            "Dossier accepté",
            value=bool(dossier.get(col_d_acc, False)) if col_d_acc else False,
        )
    with s4:
        date_accepte = st.date_input(
            "Date acceptation",
            _to_date(dossier.get(col_dt_acc)) if col_dt_acc else None,
        )

    s5, s6 = st.columns(2)
    with s5:
        dossier_refuse = st.checkbox(
            "Dossier refusé",
            value=bool(dossier.get(col_d_ref, False)) if col_d_ref else False,
        )
    with s6:
        date_refuse = st.date_input(
            "Date refus",
            _to_date(dossier.get(col_dt_ref)) if col_dt_ref else None,
        )

    s7, s8 = st.columns(2)
    with s7:
        dossier_annule = st.checkbox(
            "Dossier Annulé",
            value=bool(dossier.get(col_d_ann, False)) if col_d_ann else False,
        )
    with s8:
        date_annule = st.date_input(
            "Date annulation",
            _to_date(dossier.get(col_dt_ann)) if col_dt_ann else None,
        )

    commentaires = st.text_area(
        "Commentaires",
        value=str(dossier.get(col_com, "")) if col_com else "",
        height=100,
    )

    # -------------------------
    # Enregistrement
    # -------------------------
    if st.button("💾 Enregistrer les modifications"):
        try:
            idx = df.index[mask][0]

            # infos générales
            df.loc[idx, "Dossier N"] = dossier_n
            df.loc[idx, "Nom"] = nom
            df.loc[idx, "Date"] = pd.to_datetime(date_creation)

            if col_cat:
                df.loc[idx, col_cat] = categorie
            if col_scat:
                df.loc[idx, col_scat] = sous_cat
            df.loc[idx, "Visa"] = visa

            # montants
            if col_mh:
                df.loc[idx, col_mh] = montant_hono
            if col_af:
                df.loc[idx, col_af] = autres_frais

            # acompte 1
            if col_ac1:
                df.loc[idx, col_ac1] = acompte1
            if col_dt_ac1:
                df.loc[idx, col_dt_ac1] = pd.to_datetime(date_acompte1)
            if col_mode:
                df.loc[idx, col_mode] = mode_paiement

            # statut / escrow / RFE
            if col_escrow:
                df.loc[idx, col_escrow] = bool(escrow_checked)
            if col_rfe:
                df.loc[idx, col_rfe] = bool(rfe)

            if col_d_env:
                df.loc[idx, col_d_env] = bool(dossier_envoye)
            if col_dt_env:
                df.loc[idx, col_dt_env] = (
                    pd.to_datetime(date_envoye) if date_envoye else None
                )

            if col_d_acc:
                df.loc[idx, col_d_acc] = bool(dossier_accepte)
            if col_dt_acc:
                df.loc[idx, col_dt_acc] = (
                    pd.to_datetime(date_accepte) if date_accepte else None
                )

            if col_d_ref:
                df.loc[idx, col_d_ref] = bool(dossier_refuse)
            if col_dt_ref:
                df.loc[idx, col_dt_ref] = (
                    pd.to_datetime(date_refuse) if date_refuse else None
                )

            if col_d_ann:
                df.loc[idx, col_d_ann] = bool(dossier_annule)
            if col_dt_ann:
                df.loc[idx, col_dt_ann] = (
                    pd.to_datetime(date_annule) if date_annule else None
                )

            if col_com:
                df.loc[idx, col_com] = commentaires

            # on remet à jour dans data/session
            data["Clients"] = df
            st.session_state["data_xlsx"] = data

            # sauvegarde via common_data
            save_all()

            st.success("✅ Modifications enregistrées.")
            st.rerun()
        except Exception as e:
            st.error(f"❌ Erreur : {e}")

