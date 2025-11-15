import streamlit as st
import pandas as pd
from common_data import ensure_loaded, save_all
import numpy as np

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

    data = ensure_loaded()
    if data is None or "Clients" not in data or data["Clients"].empty:
        st.warning("Aucun fichier chargé — veuillez l'importer via l’onglet 📄 Fichiers.")
        return

    df = data["Clients"]

    # --- Sélection du client par NOM
    noms = df["Nom"].fillna("").astype(str).unique().tolist()
    selected_nom = st.selectbox("Sélectionnez le nom du client", noms)
    mask = df["Nom"].astype(str) == selected_nom

    if not mask.any():
        st.error("Client non trouvé.")
        return

    idx = df[mask].index[0]
    dossier = df.loc[idx]

    # --- Affichage/MODIFICATION des champs principaux ---
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
        st.markdown(f"**Total facturé : {total_facture:.2f} US $**")
    
    # --- Gestion dynamique des acomptes ---
    st.subheader("Paiements et Acomptes")

    # Liste des acomptes existants dans df
    max_acompte = 1
    reste = total_facture
    acomptes = []
    for i in range(1, 10):  # limite à 10 acomptes pour éviter boucle infinie
        acompte_col = f"Acompte {i}"
        date_col = f"Date Acompte {i}"
        if acompte_col in df.columns:
            v = _to_float(dossier.get(acompte_col, 0.0))
            reste -= v
            acomptes.append((
                st.number_input(f"{acompte_col} (US $)", min_value=0.0, value=v, step=10.0, key=f"acompte_{i}"),
                st.date_input(f"{date_col}", _to_date(dossier.get(date_col)), key=f"date_acompte_{i}")
            ))
            max_acompte = i
        else:
            break

    st.markdown(f"**Reste à payer : {reste:.2f} US $**")
    # Si reste > 0, proposer un nouvel acompte
    if reste > 0:
        if st.button("Ajouter un nouvel acompte"):
            new_col = f"Acompte {max_acompte+1}"
            new_date_col = f"Date Acompte {max_acompte+1}"
            # Ajoute les colonnes dans df si inexistantes
            if new_col not in df.columns:
                df[new_col] = 0.0
            if new_date_col not in df.columns:
                df[new_date_col] = ""
            st.success("Acompte supplémentaire ajouté. Veuillez rerun l'onglet pour le remplir")
            save_all()
            st.rerun()

    # --- Statuts sans cases à cocher ---
    st.subheader("Statut et dates de suivi")
    colA, colB = st.columns(2)
    with colA:
        date_envoye = st.date_input("Date dossier envoyé", _to_date(dossier.get("Date envoi")))
        date_accepte = st.date_input("Date dossier accepté", _to_date(dossier.get("Date acceptation")))
        date_refuse = st.date_input("Date dossier refusé", _to_date(dossier.get("Date refus")))
        date_annule = st.date_input("Date dossier annulé", _to_date(dossier.get("Date annulation")))
        date_rfe = st.date_input("Date RFE/ réponse", _to_date(dossier.get("Date Acompte 1"))) # Si tu utilises une colonne dédiée à la date de la réponse RFE, change ici
    with colB:
        rfe = st.checkbox("RFE", value=bool(dossier.get("RFE", False)))
        commentaires = st.text_area("Commentaires", value=str(dossier.get("Commentaires", "")), height=80)

    # --- Boutons de modification/suppression ---
    st.subheader("Actions")
    modif = st.button("💾 Enregistrer les modifications")
    supp = st.button("🗑️ Supprimer ce dossier")

    if modif:
        # Met à jour les champs
        df.loc[idx, "Nom"] = nom
        df.loc[idx, "Catégories"] = categorie
        df.loc[idx, "Sous-catégories"] = sous_categorie
        df.loc[idx, "Visa"] = visa
        df.loc[idx, "Montant honoraires (US $)"] = montant_hono
        df.loc[idx, "Autres frais (US $)"] = autres_frais
        for i, (acompte_val, date_val) in enumerate(acomptes, start=1):
            df.loc[idx, f"Acompte {i}"] = acompte_val
            df.loc[idx, f"Date Acompte {i}"] = pd.to_datetime(date_val)
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
        # Supprime la ligne
        df = df.drop(idx)
        data["Clients"] = df
        st.session_state["data_xlsx"] = data
        save_all()
        st.success(f"Dossier '{nom}' supprimé.")
        st.rerun()
