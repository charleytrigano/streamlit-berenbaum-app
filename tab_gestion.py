import streamlit as st
import pandas as pd
from datetime import date
from common_data import ensure_loaded, save_all, CLIENTS_COLUMNS


def _to_date(value):
    if pd.isna(value):
        return date.today()
    if isinstance(value, pd.Timestamp):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return pd.to_datetime(value).date()
    except Exception:
        return date.today()


def _to_bool(value):
    if isinstance(value, bool):
        return value
    s = str(value).strip().lower()
    return s in ("1", "true", "vrai", "oui", "yes", "x")


def tab_gestion():
    st.header("✏️ / 🗑️ Gestion des dossiers")

    data = ensure_loaded()
    if data is None:
        st.warning("Aucune donnée chargée. Importe le fichier via 📄 Fichiers.")
        return

    df = data["Clients"].copy()
    if df.empty:
        st.info("Aucun dossier dans la feuille Clients.")
        return

    # Sélection du dossier
    csel1, csel2 = st.columns(2)
    with csel1:
        dossier_options = sorted(df["Dossier N"].astype(str).unique().tolist())
        dossier_n_sel = st.selectbox("Par Dossier N°", [""] + dossier_options, key="gest_sel_num")
    with csel2:
        nom_options = sorted(df["Nom"].astype(str).unique().tolist())
        nom_sel = st.selectbox("Par Nom", [""] + nom_options, key="gest_sel_nom")

    selected_index = None
    if dossier_n_sel:
        # priorité à Dossier N
        selected_index = df.index[df["Dossier N"].astype(str) == dossier_n_sel].tolist()
    elif nom_sel:
        selected_index = df.index[df["Nom"].astype(str) == nom_sel].tolist()

    if not selected_index:
        st.info("Sélectionne un dossier pour le modifier.")
        return

    idx = selected_index[0]
    dossier = df.loc[idx]

    st.markdown(f"### Dossier **{dossier['Dossier N']}** – {dossier['Nom']}")

    # --- Informations générales ---
    c1, c2, c3 = st.columns(3)
    with c1:
        nom = st.text_input("Nom", value=str(dossier.get("Nom", "")), key="gest_nom")
    with c2:
        date_creation = st.date_input(
            "Date (création)",
            value=_to_date(dossier.get("Date")),
            key="gest_date_creation",
        )
    with c3:
        visa = st.text_input("Visa", value=str(dossier.get("Visa", "")), key="gest_visa")

    # --- Classification ---
    st.subheader("Classification")
    c4, c5 = st.columns(2)
    with c4:
        categorie = st.text_input("Catégories", value=str(dossier.get("Catégories", "")), key="gest_cat")
    with c5:
        sous_cat = st.text_input("Sous-catégories", value=str(dossier.get("Sous-catégories", "")), key="gest_sous_cat")

    # --- Montants & acomptes ---
    st.subheader("Montants & acomptes")

    c6, c7 = st.columns(2)
    with c6:
        montant_hono = st.number_input(
            "Montant honoraires (US $)",
            min_value=0.0,
            value=float(pd.to_numeric(dossier.get("Montant honoraires (US $)"), errors="coerce") or 0.0),
            step=50.0,
            key="gest_montant_hono",
        )
    with c7:
        autres_frais = st.number_input(
            "Autres frais (US $)",
            min_value=0.0,
            value=float(pd.to_numeric(dossier.get("Autres frais (US $)"), errors="coerce") or 0.0),
            step=10.0,
            key="gest_autres_frais",
        )

    st.markdown("#### Acomptes")

    # Acompte 1
    cA1, cA2, cA3 = st.columns(3)
    with cA1:
        acompte1 = st.number_input(
            "Acompte 1",
            min_value=0.0,
            value=float(pd.to_numeric(dossier.get("Acompte 1"), errors="coerce") or 0.0),
            step=10.0,
            key="gest_ac1",
        )
    with cA2:
        date_ac1 = st.date_input(
            "Date Acompte 1",
            value=_to_date(dossier.get("Date Acompte 1")),
            key="gest_date_ac1",
        )
    with cA3:
        mode_paie = st.selectbox(
            "mode de paiement",
            ["", "Chèque", "Virement", "Carte bancaire", "Venmo"],
            index=["", "Chèque", "Virement", "Carte bancaire", "Venmo"].index(
                str(dossier.get("mode de paiement", ""))
            ) if str(dossier.get("mode de paiement", "")) in ["", "Chèque", "Virement", "Carte bancaire", "Venmo"] else 0,
            key="gest_mode_paiement",
        )

    # Acompte 2
    cB1, cB2 = st.columns(2)
    with cB1:
        acompte2 = st.number_input(
            "Acompte 2",
            min_value=0.0,
            value=float(pd.to_numeric(dossier.get("Acompte 2"), errors="coerce") or 0.0),
            step=10.0,
            key="gest_ac2",
        )
    with cB2:
        date_ac2 = st.date_input(
            "Date Acompte 2",
            value=_to_date(dossier.get("Date Acompte 2")),
            key="gest_date_ac2",
        )

    # Acompte 3
    cC1, cC2 = st.columns(2)
    with cC1:
        acompte3 = st.number_input(
            "Acompte 3",
            min_value=0.0,
            value=float(pd.to_numeric(dossier.get("Acompte 3"), errors="coerce") or 0.0),
            step=10.0,
            key="gest_ac3",
        )
    with cC2:
        date_ac3 = st.date_input(
            "Date Acompte 3",
            value=_to_date(dossier.get("Date Acompte 3")),
            key="gest_date_ac3",
        )

    # Acompte 4
    cD1, cD2 = st.columns(2)
    with cD1:
        acompte4 = st.number_input(
            "Acompte 4",
            min_value=0.0,
            value=float(pd.to_numeric(dossier.get("Acompte 4"), errors="coerce") or 0.0),
            step=10.0,
            key="gest_ac4",
        )
    with cD2:
        date_ac4 = st.date_input(
            "Date Acompte 4",
            value=_to_date(dossier.get("Date Acompte 4")),
            key="gest_date_ac4",
        )

    # --- Statut / Escrow / RFE ---
    st.subheader("Statut du dossier")

    cE1, cE2 = st.columns(2)
    with cE1:
        escrow_manual = st.checkbox("Escrow (manuel)", value=_to_bool(dossier.get("Escrow")), key="gest_escrow_manual")
    with cE2:
        rfe = st.checkbox("RFE", value=_to_bool(dossier.get("RFE")), key="gest_rfe")

    cF1, cF2 = st.columns(2)
    with cF1:
        dos_envoye = st.checkbox("Dossier envoyé", value=_to_bool(dossier.get("Dossier envoyé")), key="gest_envoye")
    with cF2:
        date_env = st.date_input(
            "Date envoi",
            value=_to_date(dossier.get("Date envoi")),
            key="gest_date_env",
        )

    cG1, cG2 = st.columns(2)
    with cG1:
        dos_accepte = st.checkbox("Dossier accepté", value=_to_bool(dossier.get("Dossier accepté")), key="gest_accepte")
    with cG2:
        date_acc = st.date_input(
            "Date acceptation",
            value=_to_date(dossier.get("Date acceptation")),
            key="gest_date_acc",
        )

    cH1, cH2 = st.columns(2)
    with cH1:
        dos_refuse = st.checkbox("Dossier refusé", value=_to_bool(dossier.get("Dossier refusé")), key="gest_refuse")
    with cH2:
        date_refus = st.date_input(
            "Date refus",
            value=_to_date(dossier.get("Date refus")),
            key="gest_date_refus",
        )

    cI1, cI2 = st.columns(2)
    with cI1:
        dos_annule = st.checkbox("Dossier Annulé", value=_to_bool(dossier.get("Dossier Annulé")), key="gest_annule")
    with cI2:
        date_annul = st.date_input(
            "Date annulation",
            value=_to_date(dossier.get("Date annulation")),
            key="gest_date_annul",
        )

    commentaires = st.text_area(
        "Commentaires",
        value=str(dossier.get("Commentaires", "")),
        key="gest_commentaires",
    )

    if st.button("💾 Enregistrer les modifications", key="gest_save_btn"):
        # Mise à jour de la ligne
        df.at[idx, "Nom"] = nom.strip()
        df.at[idx, "Date"] = pd.to_datetime(date_creation)
        df.at[idx, "Visa"] = visa.strip()
        df.at[idx, "Catégories"] = categorie.strip()
        df.at[idx, "Sous-catégories"] = sous_cat.strip()

        df.at[idx, "Montant honoraires (US $)"] = float(montant_hono)
        df.at[idx, "Autres frais (US $)"] = float(autres_frais)

        df.at[idx, "Acompte 1"] = float(acompte1)
        df.at[idx, "Date Acompte 1"] = pd.to_datetime(date_ac1)
        df.at[idx, "mode de paiement"] = mode_paie

        df.at[idx, "Acompte 2"] = float(acompte2)
        df.at[idx, "Date Acompte 2"] = pd.to_datetime(date_ac2)
        df.at[idx, "Acompte 3"] = float(acompte3)
        df.at[idx, "Date Acompte 3"] = pd.to_datetime(date_ac3)
        df.at[idx, "Acompte 4"] = float(acompte4)
        df.at[idx, "Date Acompte 4"] = pd.to_datetime(date_ac4)

        df.at[idx, "Dossier envoyé"] = bool(dos_envoye)
        df.at[idx, "Date envoi"] = pd.to_datetime(date_env)
        df.at[idx, "Dossier accepté"] = bool(dos_accepte)
        df.at[idx, "Date acceptation"] = pd.to_datetime(date_acc)
        df.at[idx, "Dossier refusé"] = bool(dos_refuse)
        df.at[idx, "Date refus"] = pd.to_datetime(date_refus)
        df.at[idx, "Dossier Annulé"] = bool(dos_annule)
        df.at[idx, "Date annulation"] = pd.to_datetime(date_annul)
        df.at[idx, "RFE"] = bool(rfe)
        df.at[idx, "Commentaires"] = commentaires

        # === LOGIQUE ESCROW AUTOMATIQUE ===
        ac1_val = float(acompte1)
        hono_val = float(montant_hono)
        escrow_auto = (ac1_val > 0) and (hono_val == 0.0)
        df.at[idx, "Escrow"] = bool(escrow_manual or escrow_auto)

        # Sauvegarde dans session + fichier mémoire
        data["Clients"] = df
        st.session_state["data_xlsx"] = data
        save_all()

        st.success(f"Dossier {dossier['Dossier N']} mis à jour.")
