import streamlit as st
import pandas as pd
import io

MAIN_FILE = "Clients BL.xlsx"

# Colonnes EXACTES de ta feuille "Clients"
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


def _ensure_clients_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Force les colonnes de Clients dans le bon ordre, en ajoutant les manquantes."""
    for col in CLIENTS_COLUMNS:
        if col not in df.columns:
            df[col] = pd.NA
    # on garde aussi les colonnes inconnues, mais on remet l'ordre officiel en premier
    known = df[CLIENTS_COLUMNS]
    extras = [c for c in df.columns if c not in CLIENTS_COLUMNS]
    if extras:
        return pd.concat([known, df[extras]], axis=1)
    return known


def load_xlsx(uploaded_file):
    """Charge un fichier XLSX uploadé et le met dans st.session_state['data_xlsx']."""
    try:
        file_bytes = uploaded_file.read()
        xls = pd.ExcelFile(io.BytesIO(file_bytes))
        data = {}

        for sheet, cols in DEFAULT_SHEETS.items():
            if sheet in xls.sheet_names:
                df = pd.read_excel(xls, sheet_name=sheet)
            else:
                df = pd.DataFrame(columns=cols)

            if sheet == "Clients":
                df = _ensure_clients_columns(df)

            data[sheet] = df

        st.session_state["data_xlsx"] = data
        st.session_state["filename"] = uploaded_file.name
        st.success(f"✅ Fichier « {uploaded_file.name} » importé.")
        return data
    except Exception as e:
        st.error(f"❌ Erreur lecture XLSX : {e}")
        return None


def save_all_local() -> bool:
    """
    Sauvegarde les données de st.session_state['data_xlsx'] dans un XLSX en mémoire,
    et stocke les bytes dans st.session_state['last_saved_file'].
    """
    if "data_xlsx" not in st.session_state:
        st.error("❌ Impossible de sauvegarder : aucune donnée chargée.")
        return False

    data_dict = st.session_state["data_xlsx"]

    try:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            for sheet, df in data_dict.items():
                if isinstance(df, pd.DataFrame) and not df.empty:
                    df.to_excel(writer, sheet_name=sheet, index=False)
                else:
                    # Excel impose au moins une feuille visible
                    pd.DataFrame({" ": []}).to_excel(writer, sheet_name=sheet, index=False)

        output.seek(0)
        st.session_state["last_saved_file"] = output.getvalue()
        st.success("💾 Sauvegarde en mémoire effectuée.")
        return True
    except Exception as e:
        st.error(f"❌ Erreur sauvegarde locale : {e}")
        return False


def save_all() -> bool:
    """Raccourci : sauvegarde ce qu'il y a dans data_xlsx."""
    return save_all_local()


def ensure_loaded():
    """Retourne le dict de feuilles ou None si rien n'est chargé."""
    return st.session_state.get("data_xlsx")
