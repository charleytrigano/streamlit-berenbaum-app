import streamlit as st
import pandas as pd

def tab_gestion():
    st.write("Test de l'appel à tab_gestion : tout fonctionne !")import streamlit as st
import pandas as pd
import os

# --- PARAMETRES DU CHEMIN FICHIER ET FEUILLE ---
DATA_PATH = r"C:\Users\charl\Mon Drive\streamlit-berenbaum-app\Clients BL.xlsx"
SHEET_NAME = "Clients"

# --- CHARGEMENT DES DONNEES ---
def ensure_loaded():
    try:
        df_clients = pd.read_excel(DATA_PATH, sheet_name=SHEET_NAME)
        st.write("Colonnes lues :", df_clients.columns.tolist())
        st.write("Aperçu des premières lignes :", df_clients.head())
        if df_clients.empty:
            st.warning("Le fichier Excel de clients est vide.")
            return None
    except Exception as e:
        st.error(f"Erreur lors du chargement Excel : {e}")
        return None
    return {"Clients": df_clients}

# --- SAUVEGARDE DES MODIFICATIONS ---
def save_data(data):
    df = data.get("Clients", pd.DataFrame())
    try:
        with pd.ExcelWriter(DATA_PATH, mode="a", if_sheet_exists="replace") as writer:
            df.to_excel(writer, sheet_name=SHEET_NAME, index=False)
    except Exception as e:
        st.error(f"Erreur sauvegarde Excel: {e}")

# --- FORMATAGE DES CASES À COCHER ---
def format_checkbox(val):
    return str(val).strip().lower() in ["true", "1", "vrai", "oui", "x", "ok"]

# --- FONCTION PRINCIPALE DE GESTION ---
def tab_gestion():
    st.header("📝 Gestion des dossiers clients")
    data = ensure_loaded()
    
    # Debug : présence des clés
    if data and "Clients" in data:
        st.write("Nombre de dossiers chargés :", len(data["Clients"]))
    else:
        st.write("La clé 'Clients' est absente ou les données sont vides.")

    if data is None or "Clients" not in data or data["Clients"].empty:
        st.error("Aucune donnée client chargée.")
        return

    df = data["Clients"].copy()
    save_flag = False

    st.info("Modifiez chaque dossier puis enregistrez vos modifications une à une.")

    # Champs à éditer (adapter à votre Excel si besoin)
    base_champs = [
        ("Dossier N", "text"),
        ("Nom", "text"),
        ("Date", "text"),
        ("Catégories", "text"),
        ("Sous-catégories", "text"),
        ("Visa", "text"),
        ("Montant honoraires (US $)", "text"),
        ("Autres frais (US $)", "text"),
        ("Acompte 1", "text"),
        ("Date Acompte 1", "text"),
        ("mode de paiement", "text"),
        ("Escrow", "checkbox"),
        ("Acompte 2", "text"),
        ("Date Acompte 2", "text"),
        ("Acompte 3", "text"),
        ("Date Acompte 3", "text"),
        ("Acompte 4", "text"),
        ("Date Acompte 4", "text"),
        ("Dossier envoyé", "checkbox"),
        ("Date envoi", "text"),
        ("Dossier accepté", "checkbox"),
        ("Date acceptation", "text"),
        ("Dossier refusé", "checkbox"),
        ("Date refus", "text"),
        ("Dossier Annulé", "checkbox"),
        ("Date annulation", "text"),
        ("RFE", "text"),
        ("Commentaires", "text"),
    ]

    for idx, row in df.iterrows():
        # Expandeur par dossier
        with st.expander(f"Dossier N°{row.get('Dossier N', idx)} — {row.get('Nom', '')}", expanded=False):
            vals = {}
            for champ, typ in base_champs:
                default = str(row.get(champ, "")) if champ in df.columns else ""
                if typ == "checkbox":
                    vals[champ] = st.checkbox(champ, value=format_checkbox(default), key=f"{champ}_{idx}")
                else:
                    vals[champ] = st.text_input(champ, value=default, key=f"{champ}_{idx}")

            # Enregistrement
            if st.button(f"Enregistrer ce dossier", key=f"save_{idx}"):
                for champ, typ in base_champs:
                    df.at[idx, champ] = vals[champ]
                save_flag = True
                st.success(f"Dossier N°{row.get('Dossier N', idx)} mis à jour.")

    if save_flag:
        data["Clients"] = df
        save_data(data)
        st.info("Les modifications ont été sauvegardées.")

    st.subheader("Aperçu synthétique des dossiers")
    synth_cols = [col for col, _ in base_champs if col in df.columns]
    st.dataframe(df[synth_cols], use_container_width=True)

