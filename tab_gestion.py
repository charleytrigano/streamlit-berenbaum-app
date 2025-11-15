import streamlit as st
import pandas as pd
from common_data import ensure_loaded, save_data

def tab_gestion():
    st.header("📝 Gestion des dossiers clients")
    data = ensure_loaded()

    if data is None or "Clients" not in data or data["Clients"].empty:
        st.warning("Aucun fichier client chargé.")
        return

    df = data["Clients"].copy()
    edited_rows = {}

    st.info("Modifiez les dossiers ci-dessous. Cliquez sur 'Enregistrer' pour sauvegarder vos changements.")

    for idx, row in df.iterrows():
        with st.expander(f"Dossier N°{row.get('Dossier N', idx)} • {row.get('Nom','')}", expanded=False):
            # Champs éditables
            nom      = st.text_input("Nom", value=str(row.get("Nom", "")), key=f"nom_{idx}")
            dossier_envoye = st.checkbox("Dossier envoyé", value=str(row.get("Dossier envoyé", "")).strip().lower() in ["true","1","vrai","oui","x","ok"], key=f"envoye_{idx}")
            date_envoi = st.text_input("Date envoi", value=str(row.get("Date envoi", "")), key=f"dateenv_{idx}")
            # Nouvelle case Escrow
            escrow_val = st.checkbox("Escrow", value=str(row.get("Escrow", "")).strip().lower() in ["true","1","vrai","oui","x","ok"], key=f"escrow_{idx}")

            # Autres champs (exemple) : Montant honoraires, Acompte 1
            honoraires = st.text_input("Montant honoraires (US $)", value=str(row.get("Montant honoraires (US $)", "")), key=f"hon_{idx}")
            acompte1 = st.text_input("Acompte 1", value=str(row.get("Acompte 1", "")), key=f"acomp1_{idx}")

            # Enregistrement des modifications
            if st.button(f"Enregistrer ce dossier", key=f"save_{idx}"):
                df.at[idx, "Nom"] = nom
                df.at[idx, "Dossier envoyé"] = dossier_envoye
                df.at[idx, "Date envoi"] = date_envoi
                df.at[idx, "Escrow"] = escrow_val
                df.at[idx, "Montant honoraires (US $)"] = honoraires
                df.at[idx, "Acompte 1"] = acompte1
                st.success(f"Dossier N°{row.get('Dossier N', idx)} mis à jour.")
                # Option de sauvegarde globale
                edited_rows[idx] = True

    # Sauvegarde finale si au moins un dossier édité
    if len(edited_rows) > 0:
        save_data(data)
        st.info("Toutes les modifications ont été sauvegardées.")

    # Affichage synthétique des dossiers
    st.subheader("Aperçu des dossiers clients")
    st.dataframe(df, use_container_width=True)
