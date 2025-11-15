import streamlit as st
import pandas as pd
import io

# Nom du fichier principal
MAIN_FILE = "Clients BL.xlsx"

# Colonnes attendues dans la feuille Clients
CLIENTS_COLUMNS = [
    "Dossier N",
    "Nom",
    "Date",
    "Catégories",
    "Sous-catégories",
    "Visa",
    "Montant honoraires (US $)",
    "Autres frais (US $)",
    "Acompte 1",
    "Date Acompte 1",
    "mode de paiement",
    "Escrow",
    "Acompte 2",
    "Date Acompte 2",
    "Acompte 3",
    "Date Acompte 3",
    "Acompte 4",
    "Date Acompte 4",
    "Dossier envoyé",
    "Date envoi",
    "Dossier accepté",
    "Date acceptation",
    "Dossier refusé",
    "Date refus",
    "Dossier Annulé",
    "Date annulation",
    "RFE",
    "Commentaires",
]

DEFAULT_SHEETS = {
    "Clients": CLIENTS_COLUMNS,
    "Visa": [],
    "ComptaCli": [],
    "Escrow": [],
}

# Petit mapping générique si certains onglets utilisent encore column_map
column_map = {
    "dossier": "Dossier N",
    "nom": "Nom",
    "date": "Date",
    "categorie": "Catégories",
    "sous_categorie": "Sous-catégories",
    "visa": "Visa",
    "honoraires": "Montant honoraires (US $)",
    "autres_frais": "Autres frais (US $)",
    "acompte1": "Acompte 1",
    "date_acompte1": "Date Acompte 1",
    "mode_paiement": "mode de paiement",
    "escrow": "Escrow",
}


def _ensure_clients_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Ajoute les colonnes manquantes dans Clients avec valeurs vides."""
    for col in CLIENTS_COLUMNS:
        if col not in df.columns:
            df[col] = pd.NA
    # On garde l'ordre officiel
    return df[CLIENTS_COLUMNS]


def load_xlsx(file_bytes: bytes):
    """Charge un XLSX uploadé via Streamlit et garantit la présence des 4 feuilles."""
    try:
        xls = pd.ExcelFile(io.BytesIO(file_bytes))
        data = {}

        # Feuille Clients
        if "Clients" in xls.sheet_names:
            df_clients = pd.read_excel(xls, sheet_name="Clients")
            df_clients = _ensure_clients_columns(df_clients)
        else:
            df_clients = pd.DataFrame(columns=CLIENTS_COLUMNS)
        data["Clients"] = df_clients

        # Autres feuilles : on charge si elles existent, sinon DataFrame vide
        for sheet in ["Visa", "ComptaCli", "Escrow"]:
            if sheet in xls.sheet_names:
                data[sheet] = pd.read_excel(xls, sheet_name=sheet)
            else:
                data[sheet] = pd.DataFrame()

        return data

    except Exception as e:
        st.error(f"Erreur lecture XLSX : {e}")
        return None


def save_all_local(data_dict: dict) -> bool:
    """
    Sauvegarde l'état actuel (data_xlsx) dans un fichier Excel en mémoire.
    Le résultat binaire est conservé dans st.session_state["last_saved_file"].
    """
    try:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            for sheet_name, df in data_dict.items():
                if not isinstance(df, pd.DataFrame):
                    df = pd.DataFrame()
                if df.empty:
                    # Pour éviter "At least one sheet must be visible"
                    df = pd.DataFrame({" ": []})
                df.to_excel(writer, sheet_name=sheet_name, index=False)

        output.seek(0)
        st.session_state["last_saved_file"] = output.getvalue()
        return True
    except Exception as e:
        st.error(f"Erreur sauvegarde locale : {e}")
        return False


def save_all():
    """
    Sauvegarde simple : utilise st.session_state["data_xlsx"] et save_all_local.
    (Signature sans argument, comme attendu par tes onglets.)
    """
    if "data_xlsx" not in st.session_state or st.session_state["data_xlsx"] is None:
        st.error("❌ Impossible de sauvegarder : aucune donnée chargée.")
        return False
    return save_all_local(st.session_state["data_xlsx"])


def ensure_loaded(filename: str):
    """
    Renvoie st.session_state['data_xlsx'] si déjà chargé.
    NE charge rien tout seul : c'est l'onglet Fichiers qui fait le upload.
    """
    if "data_xlsx" in st.session_state and st.session_state["data_xlsx"] is not None:
        return st.session_state["data_xlsx"]
    st.warning("⚠️ Fichier non chargé — importe d’abord le XLSX via l’onglet 📄 Fichiers.")
    return None
