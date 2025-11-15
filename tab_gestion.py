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
    
    # Paiements : acomptes 1 et 2 sur la 1ère ligne, 3 et 4 sur la 2ème ligne
    st.subheader("Paiements / acomptes")

    accomptes_data = []
    # Acomptes 1 et 2
    ac1, ac2 = st.columns(2)
    with ac1:
        acompte1 = st.number_input("Acompte 1 (US $)", min_value=0.0, value=_to_float(dossier.get("Acompte 1", 0.0)), step=10.0)
        date_acompte1 = st.date_input("Date Acompte 1", _to_date(dossier.get("Date Acompte 1"), default=datetime.date.today()), key="date_acompte_1")
        mode1 = st.text_input("Mode règlement Acompte 1", str(dossier.get("Mode de règlement 1", dossier.get("mode de paiement", ""))))
        accomptes_data.append((acompte1, date_acompte1, mode1))
    with ac2:
        acompte2 = st.number_input("Acompte 2 (US $)", min_value=0.0, value=_to_float(dossier.get("Acompte 2", 0.0)), step=10.0)
        date_acompte2 = st.date_input("Date Acompte 2", _to_date(dossier.get("Date Acompte 2"), default=datetime.date.today()), key="date_acompte_2")
        mode2 = st.text_input("Mode règlement Acompte 2", str(dossier.get("Mode de règlement 2", "")))
        accomptes_data.append((acompte2, date_acompte2, mode2))

    # Acomptes 3 et 4
    ac3, ac4 = st.columns(2)
    with ac3:
        acompte3 = st.number_input("Acompte 3 (US $)", min_value=0.0, value=_to_float(dossier.get("Acompte 3", 0.0)), step=10.0)
        date_acompte3 = st.date_input("Date Acompte 3", _to_date(dossier.get("Date Acompte 3"), default=datetime.date.today()), key="date_acompte_3")
        mode3 = st.text_input("Mode règlement Acompte 3", str(dossier.get("Mode de règlement 3", "")))
        accomptes_data.append((acompte3, date_acompte3, mode3))
    with ac4:
        acompte4 = st.number_input("Acompte 4 (US $)", min_value=0.0, value=_to_float(dossier.get("Acompte 4", 0.0)), step=10.0)
        date_acompte4 = st.date_input("Date Acompte 4", _to_date(dossier.get("Date Acompte 4"), default=datetime.date.today()), key="date_acompte_4")
        mode4 = st.text_input("Mode règlement Acompte 4", str(dossier.get("Mode de règlement 4", "")))
        accomptes_data.append((acompte4, date_acompte4, mode4))

    # Calcul du reste à payer
    reste_total = total_facture - sum(x[0] for x in accomptes_data)
    st.markdown(f"**Reste à payer : {reste_total:.2f} US $**")

    # Statuts & suivi
    st.subheader("Statut & suivi du dossier")
    su1, su2, su3, su4 = st.columns(4)
    with su1:
        dossier_envoye = st.checkbox("Dossier envoyé", value=bool(dossier.get("Dossier envoyé", False)))
        date_envoye = st.date_input("Date envoi", _to_date(dossier.get("Date envoi"), default=datetime.date.today()), key="date_envoye")
    with su2:
        dossier_accepte = st.checkbox("Dossier accepté", value=bool(dossier.get("Dossier accepté", False)))
        date_accepte = st.date_input("Date acceptation", _to_date(dossier.get("Date acceptation"), default=datetime.date.today()), key="date_accepte")
    with su3:
        dossier_refuse = st.checkbox("Dossier refusé", value=bool(dossier.get("Dossier refusé", False)))
        date_refuse = st.date_input("Date refus", _to_date(dossier.get("Date refus"), default=datetime.date.today()), key="date_refuse")
    with su4:
        dossier_annule = st.checkbox("Dossier annulé", value=bool(dossier.get("Dossier Annulé", False)))
        date_annule = st.date_input("Date annulation", _to_date(dossier.get("Date annulation"), default=datetime.date.today()), key="date_annulation")

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
        for i, (acompte_val, date_val, mode_val) in enumerate(accomptes_data, start=1):
            df.loc[idx, f"Acompte {i}"] = acompte_val
            df.loc[idx, f"Date Acompte {i}"] = pd.to_datetime(date_val) if date_val else ""
            df.loc[idx, f"Mode de règlement {i}"] = mode_val
        df.loc[idx, "Dossier envoyé"] = bool(dossier_envoye)
        df.loc[idx, "Date envoi"] = pd.to_datetime(date_envoye) if date_envoye else ""
        df.loc[idx, "Dossier accepté"] = bool(dossier_accepte)
        df.loc[idx, "Date acceptation"] = pd.to_datetime(date_accepte) if date_accepte else ""
        df.loc[idx, "Dossier refusé"] = bool(dossier_refuse)
        df.loc[idx, "Date refus"] = pd.to_datetime(date_refuse) if date_refuse else ""
        df.loc[idx, "Dossier Annulé"] = bool(dossier_annule)
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
