import streamlit as st
import pandas as pd
import io

MAIN_FILE = "Clients BL.xlsx"

# Définition des colonnes exactes
DEFAULT_CLIENTS_COLUMNS = [
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
    "Commentaires"
]

DEFAULT_SHEETS = {
    "Clients": DEFAULT_CLIENTS_COLUMNS,
    "Visa": [],
    "ComptaCli": [],
    "Escrow": []
}


# --------------- LECTURE FICHIER -----------------

def load_xlsx(file_bytes):
    """Charge correctement un XLSX uploadé sur Streamlit."""
    try:
        file_bytes = io.BytesIO(file_bytes)

        xls = pd.ExcelFile(file_bytes)
        data = {}

        for sheet, cols in DEFAULT_SHEETS.items():
            if sheet in xls.sheet_names:
                df = pd.read_excel(xls, sheet_name=sheet)

                # Ajoute les colonnes manquantes (sécurité)
                for c in cols:
                    if c not in df.columns:
                        df[c] = ""
            else:
                df = pd.DataFrame(columns=cols)

            data[sheet] = df

        return data

    except Exception as e:
        st.error(f"❌ Erreur lecture XLSX : {e}")
        return None


# ----------------- SAUVEGARDE --------------------

def save_all():
    """Sauvegarde dans session_state['last_saved_file'] un excel propre."""
    try:
        if "data_xlsx" not in st.session_state:
            st.error("Aucune donnée à sauvegarder.")
            return False

        data = st.session_state["data_xlsx"]

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            for sheet, df in data.items():
                if df.empty:
                    df = pd.DataFrame({" ": []})
                df.to_excel(writer, sheet_name=sheet, index=False)

        output.seek(0)
        st.session_state["last_saved_file"] = output.getvalue()
        st.success("💾 Sauvegarde effectuée.")
        return True

    except Exception as e:
        st.error(f"❌ Erreur sauvegarde : {e}")
        return False


# ----------------- CHARGEMENT ---------------------

def ensure_loaded():
    """Retourne data_xlsx si chargé, sinon avertit."""
    if "data_xlsx" in st.session_state:
        return st.session_state["data_xlsx"]

    st.warning("⚠️ Aucun fichier chargé — utilisez l’onglet Fichiers.")
    return None
