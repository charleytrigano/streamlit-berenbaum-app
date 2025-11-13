# common_data.py
import pandas as pd
from typing import Dict

MAIN_FILE = "Clients BL.xlsx"


def load_xlsx(path: str = MAIN_FILE) -> Dict[str, pd.DataFrame]:
    """Charge toutes les feuilles du fichier Excel en dict {nom_feuille: DataFrame}."""
    xls = pd.ExcelFile(path)
    data: Dict[str, pd.DataFrame] = {}
    for sheet in xls.sheet_names:
        data[sheet] = pd.read_excel(xls, sheet_name=sheet)
    return data


def ensure_loaded(filename: str = MAIN_FILE):
    """
    Retourne st.session_state["data_xlsx"].
    Si vide, essaie de charger le fichier Excel local.
    """
    import streamlit as st

    # Si déjà chargé en mémoire, on réutilise
    if "data_xlsx" in st.session_state and st.session_state["data_xlsx"]:
        return st.session_state["data_xlsx"]

    # Sinon on tente de charger depuis le fichier du repo
    try:
        data = load_xlsx(filename)
    except Exception as e:
        st.warning(f"⚠️ Impossible de charger '{filename}' automatiquement : {e}")
        data = {}

    st.session_state["data_xlsx"] = data
    return data


def save_all_local(filename: str = MAIN_FILE):
    """
    (Optionnel) Sauvegarde locale dans le conteneur Streamlit Cloud.
    Ça ne persiste pas entre redéploiements, mais on le garde si besoin.
    """
    import streamlit as st
    import io

    data = st.session_state.get("data_xlsx")
    if not data:
        st.warning("⚠️ Aucune donnée en mémoire à sauvegarder.")
        return

    try:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            for sheet, df in data.items():
                # On force la feuille visible (évite l’erreur 'At least one sheet must be visible')
                df.to_excel(writer, sheet_name=sheet, index=False)

        # Écriture dans un fichier local
        with open(filename, "wb") as f:
            f.write(output.getvalue())

        st.success(f"💾 Fichier sauvegardé localement sous le nom : {filename}")
    except Exception as e:
        st.error(f"❌ Erreur lors de la sauvegarde locale : {e}")
