import streamlit as st
import pandas as pd
import os

# Chemin de stockage (à adapter selon ton infra)
DATA_PATH = "clients.xlsx"  # Peut être modifié

def ensure_loaded():
    # Charge ou crée le DataFrame client
    try:
        df_clients = pd.read_excel(DATA_PATH)
    except Exception:
        df_clients = pd.DataFrame()
    return {"Clients": df_clients}

def save_data(data):
    df = data.get("Clients", pd.DataFrame())
    df.to_excel(DATA_PATH, index=False)

def format_checkbox(val):
    return str(val).strip().lower() in ["true", "1", "vrai", "oui", "x", "ok"]

def tab_gestion():
    st.header("📝 Gestion des dossiers clients")
    data = ensure_loaded()
    if data is None or "Clients" not in data or data["Clients"].empty:
        st.error("Aucune donnée client chargée.")
        return

    df = data["Clients"].copy()
    save_flag = False

    st.info("Modifiez chaque dossier puis enregistrez vos modifications une à une.")

    # Liste des champs à éditer
    base_champs = [
        ("Dossier N", "text"),
        ("Nom", "text"),
        ("Catégories", "text"),
        ("Sous-catégories", "text"),
        ("Visa", "text"),
        ("Statut", "text"),
        ("Commentaires", "text"),
        ("Pièces reçues", "text"),
        ("Pièces manquantes", "text"),
        ("Montant honoraires (US $)", "text"),
        ("Autres frais (US $)", "text"),
        ("Acompte 1", "text"),
        ("Date Acompte 1", "text"),
        ("Acompte 2", "text"),
        ("Date Acompte 2", "text"),
        ("Acompte 3", "text"),
        ("Date Acompte 3", "text"),
        ("Acompte 4", "text"),
        ("Date Acompte 4", "text"),
        ("Dossier envoyé", "checkbox"),
        ("Date envoi", "text"),
        ("Escrow", "checkbox"),
        # Ajoute ici tout champ supplémentaire
    ]

    for idx, row in df.iterrows():
        with st.expander(f"Dossier N°{row.get('Dossier N', idx)} — {row.get('Nom', '')}", expanded=False):
            vals = {}
            for champ, typ in base_champs:
                default = str(row.get(champ, ""))
                if typ == "checkbox":
                    vals[champ] = st.checkbox(
                        champ,
                        value=format_checkbox(default),
                        key=f"{champ}_{idx}")
                else:
                    vals[champ] = st.text_input(champ, value=default, key=f"{champ}_{idx}")

            # Enregistrement
            if st.button(f"Enregistrer ce dossier", key=f"save_{idx}"):
                for champ, typ in base_champs:
                    if typ == "checkbox":
                        df.at[idx, champ] = vals[champ]
                    else:
                        df.at[idx, champ] = vals[champ]
                save_flag = True
                st.success(f"Dossier N°{row.get('Dossier N', idx)} mis à jour.")

    if save_flag:
        data["Clients"] = df
        save_data(data)
        st.info("Les modifications ont été sauvegardées.")

    # Aperçu synthétique
    st.subheader("Aperçu synthétique des dossiers")
    # Choix des colonnes à afficher en synthèse
    synth_cols = [
        "Dossier N", "Nom", "Statut",
        "Montant honoraires (US $)", "Autres frais (US $)",
        "Acompte 1", "Acompte 2", "Acompte 3", "Acompte 4",
        "Dossier envoyé", "Escrow"
    ]
    available_columns = [col for col in synth_cols if col in df.columns]
    st.dataframe(df[available_columns], use_container_width=True)
