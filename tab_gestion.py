import streamlit as st
import pandas as pd
import datetime
from common_data import ensure_loaded, save_all

def _to_float(value):
    try:
        s = str(value).replace("\u00A0", "").replace(" ", "").replace(",", ".")
        return float(s) if s not in ("", "nan", "None") else 0.0
    except Exception:
        return 0.0

def _to_date(value, default=None):
    """Convertit Excel vers date ou retourne une date du jour si absent."""
    if value is None or str(value).strip() == "" or pd.isna(value):
        return default if default else datetime.date.today()
    try:
        d = pd.to_datetime(value)
        if pd.isna(d):
            return default if default else datetime.date.today()
        return d.date()
    except Exception:
        return default if default else datetime.date.today()

def tab_gestion():
    st.header("✏️ / 🗑️ Gestion d’un dossier")

    data = ensure_loaded()
    if data is None or "Clients" not in data or data["Clients"].empty:
        st.info("Aucun client enregistré. Importez un fichier via 📄 Fichiers et ajoutez des dossiers via ➕ Ajouter.")
        return
    
    df = data["Clients"]
    if "Nom" not in df.columns or df["Nom"].dropna().empty:
        st.info("Aucun client avec un nom trouvé dans la feuille Clients.")
        return
    
    noms = df["Nom"].fillna("").astype(str).tolist()
    selected_nom = st.selectbox("Sélectionnez un client par nom", noms)
    mask = df["Nom"].astype(str) == selected_nom
    if not mask.any():
        st.warning("Aucun dossier trouvé pour ce nom.")
        return
    
    idx = df[mask].index[0]
    dossier = df.loc[idx]

    # Infos principales
    st.subheader("Informations générales")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        nom = st.text_input("Nom", str(dossier["Nom"]))
    with col2:
        categorie = st.text_input("Catégories", str(dossier.get("Catégories", "")))
    with col3:
        sous_categorie = st.text_input("Sous-catégories", str(dossier.get("Sous-catégories", "")))
    with col4:
        visa = st.text_input("Visa", str(dossier.get("Visa", "")))

    col5, col6, col7 = st.columns(3)
    with col5:
        montant_hono = st.number_input("Montant honoraires (US $)", min_value=0.0, value=_to_float(dossier.get("Montant honoraires (US $)", 0.0)), step=50.0)
    with col6:
        autres_frais = st.number_input("Autres frais (US $)", min_value=0.0, value=_to_float(dossier.get("Autres frais (US $)", 0.0)), step=10.0)
    with col7:
        total_facture = montant_hono + autres_frais
        st.markdown(f"**Total facturé : {total_facture:.2f} US $**")
    
    # Paiements dynamiques
    st.subheader("Paiements / acomptes")
    acomptes, reste = [], total_facture
    for i in range(1, 10):  # max 10 acomptes
        acompte_col = f"Acompte {i}"
        date_col = f"Date Acompte {i}"
        if acompte_col in df.columns:
            v = _to_float(dossier.get(acompte_col, 0.0))
            d = _to_date(dossier.get(date_col), default=datetime.date.today())
            reste -= v
            acomptes.append((
                st.number_input(f"{acompte_col} (US $)", min_value=0.0, value=v, step=10.0, key=f"acompte_{i}"),
                st.date_input(f"{date_col}", d, key=f"date_acompte_{i}")
            ))
        else:
            break

    st.markdown(f"**Reste à payer : {reste:.2f} US $**")

    if reste > 0 and st.button("Ajouter un acompte supplémentaire"):
        next_col = f"Acompte {len(acomptes)+1}"
        next_date_col = f"Date Acompte {len(acomptes)+1}"
        if next_col not in df.columns:
            df[next_col] = 0.0
        if next_date_col not in df.columns:
            df[next_date_col] = ""
        st.success("Acompte supplémentaire ajouté. Relancez l’onglet pour le remplir.")
        save_all()
        st.rerun()

    # Statuts & dates
    st.subheader("Dates de suivi")
    colA, colB = st.columns(2)
    with colA:
        date_envoye = st.date_input("Date dossier envoyé", _to_date(dossier.get("Date envoi"), default=datetime.date.today()))
        date_accepte = st.date_input("Date dossier accepté", _to_date(dossier.get("Date acceptation"), default=datetime.date.today()))
        date_refuse = st.date_input("Date dossier refusé", _to_date(dossier.get("Date refus"), default=datetime.date.today()))
        date_annule = st.date_input("Date dossier annulé", _to_date(dossier.get("Date annulation"), default=datetime.date.today()))
        date_rfe = st.date_input("Date RFE", _to_date(dossier.get("Date Acompte 1"), default=datetime.date.today())) # adapte si tu veux une autre colonne

    with colB:
        rfe = st.checkbox("RFE", value=bool(dossier.get("RFE", False)))
        commentaires = st.text_area("Commentaires", value=str(dossier.get("Commentaires", "")), height=80)

    st.subheader("Actions")
    modif = st.button("💾 Enregistrer les modifications")
    supp = st.button("🗑️ Supprimer ce dossier")

    if modif:
        df.loc[idx, "Nom"] = nom
        df.loc[idx, "Catégories"] = categorie
        df.loc[idx, "Sous-catégories"] = sous_categorie
        df.loc[idx, "Visa"] = visa
        df.loc[idx, "Montant honoraires (US $)"] = montant_hono
        df.loc[idx, "Autres frais (US $)"] = autres_frais
        for i, (acompte_val, date_val) in enumerate(acomptes, start=1):
            df.loc[idx, f"Acompte {i}"] = acompte_val
            df.loc[idx, f"Date Acompte {i}"] = pd.to_datetime(date_val) if date_val else ""
        df.loc[idx, "Date envoi"] = pd.to_datetime(date_envoye) if date_envoye else ""
        df.loc[idx, "Date acceptation"] = pd.to_datetime(date_accepte) if date_accepte else ""
        df.loc[idx, "Date refus"] = pd.to_datetime(date_refuse) if date_refuse else ""
        df.loc[idx, "Date annulation"] = pd.to_datetime(date_annule) if date_annule else ""
        df.loc[idx, "RFE"] = bool(rfe)
        df.loc[idx, "Commentaires"] = commentaires
        st.session_state["data_xlsx"] = data
        save_all()
        st.success("✅ Modifications enregistrées.")
        st.rerun()

    if supp:
        df = df.drop(idx)
        data["Clients"] = df
        st.session_state["data_xlsx"] = data
        save_all()
        st.success(f"Dossier '{nom}' supprimé.")
        st.rerun()
