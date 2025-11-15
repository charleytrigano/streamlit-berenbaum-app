import streamlit as st
import pandas as pd
from common_data import ensure_loaded, save_data

def tab_gestion():
    st.header("📝 Gestion des dossiers clients")

    # Chargement des données clients
    data = ensure_loaded()
    if data is None or "Clients" not in data or data["Clients"].empty:
        st.error("Aucune donnée client chargée.")
        return

    df = data["Clients"].copy()
    save_flag = False  # Pour savoir si on a enregistré au moins une modification

    st.info("Modifiez les dossiers ci-dessous. Cliquez sur 'Enregistrer ce dossier' à chaque modification.")

    # Boucle sur les dossiers
    for idx, row in df.iterrows():
        with st.expander(f"Dossier N°{row.get('Dossier N', idx)} — {row.get('Nom', '')}", expanded=False):

            nom      = st.text_input("Nom", value=str(row.get("Nom", "")), key=f"nom_{idx}")
            categorie = st.text_input("Catégories", value=str(row.get("Catégories", "")), key=f"cat_{idx}")
            sous_cat = st.text_input("Sous-catégories", value=str(row.get("Sous-catégories", "")), key=f"souscat_{idx}")
            visa = st.text_input("Visa", value=str(row.get("Visa", "")), key=f"visa_{idx}")

            honoraires = st.text_input("Montant honoraires (US $)", value=str(row.get("Montant honoraires (US $)", "")), key=f"hon_{idx}")
            autres_frais = st.text_input("Autres frais (US $)", value=str(row.get("Autres frais (US $)", "")), key=f"frais_{idx}")

            acompte1 = st.text_input("Acompte 1", value=str(row.get("Acompte 1", "")), key=f"acomp1_{idx}")
            date_acompte1 = st.text_input("Date Acompte 1", value=str(row.get("Date Acompte 1", "")), key=f"dateacomp1_{idx}")

            dossier_envoye = st.checkbox("Dossier envoyé", value=str(row.get("Dossier envoyé", "")).strip().lower() in ["true", "1", "vrai", "oui", "x", "ok"], key=f"envoye_{idx}")
            date_envoi = st.text_input("Date envoi", value=str(row.get("Date envoi", "")), key=f"dateenv_{idx}")

            # Nouvelle case à cocher Escrow (édition directe)
            escrow_val = st.checkbox("Escrow", value=str(row.get("Escrow", "")).strip().lower() in ["true", "1", "vrai", "oui", "x", "ok"], key=f"escrow_{idx}")

            # Optionnel : autres acomptes, champs personnalisés ici...

            # Enregistrement du dossier
            if st.button(f"Enregistrer ce dossier", key=f"save_{idx}"):
                df.at[idx, "Nom"] = nom
                df.at[idx, "Catégories"] = categorie
                df.at[idx, "Sous-catégories"] = sous_cat
                df.at[idx, "Visa"] = visa
                df.at[idx, "Montant honoraires (US $)"] = honoraires
                df.at[idx, "Autres frais (US $)"] = autres_frais
                df.at[idx, "Acompte 1"] = acompte1
                df.at[idx, "Date Acompte 1"] = date_acompte1
                df.at[idx, "Dossier envoyé"] = dossier_envoye
                df.at[idx, "Date envoi"] = date_envoi
                df.at[idx, "Escrow"] = escrow_val
                save_flag = True
                st.success(f"Dossier N°{row.get('Dossier N', idx)} mis à jour.")

    # Sauvegarde globale si au moins un enregistrement effectué
    if save_flag:
        data["Clients"] = df
        save_data(data)
        st.info("Les modifications ont été sauvegardées.")

    # Aperçu synthétique du fichier clients
    st.subheader("Aperçu synthétique des dossiers")
    st.dataframe(df, use_container_width=True)
