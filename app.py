import streamlit as st
import pandas as pd
import os

# ===================== CONFIGURATION GÉNÉRALE =====================
st.set_page_config(page_title="Visa Manager", layout="wide", page_icon="🛂")

EXCEL_FILE = "Clients BL.xlsx"

# ===================== CHARGEMENT DU FICHIER EXCEL =====================
@st.cache_data
def load_excel(file_path):
    if not os.path.exists(file_path):
        st.error(f"❌ Le fichier '{file_path}' est introuvable dans le dépôt Streamlit Cloud.")
        return {}
    try:
        xls = pd.ExcelFile(file_path)
        data = {sheet: pd.read_excel(xls, sheet_name=sheet) for sheet in xls.sheet_names}
        st.success(f"✅ Fichier Excel chargé ({len(data)} feuilles détectées)")
        return data
    except Exception as e:
        st.error(f"Erreur lors du chargement de l'Excel : {e}")
        return {}

# Charger les données une fois
if "data_xlsx" not in st.session_state:
    st.session_state["data_xlsx"] = load_excel(EXCEL_FILE)

data = st.session_state["data_xlsx"]

# ===================== BARRE D’ONGLETS =====================
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/744/744465.png", width=70)
st.sidebar.title("🛂 Visa Manager")

tabs = st.tabs([
    "📄 Fichiers",
    "📊 Dashboard",
    "📈 Analyses",
    "➕ Ajouter",
    "✏️ / 🗑️ Gestion",
    "💳 Compta Clients",
    "🛡️ Escrow",
    "⚙️ Paramètres"
])

# ===================== IMPORT DES MODULES =====================
from tab_fichiers import tab_fichiers
from tab_dashboard import tab_dashboard
from tab_analyses import tab_analyses
from tab_ajouter import tab_ajouter
from tab_gestion import tab_gestion
from tab_compta import tab_compta
from tab_escrow import tab_escrow
from tab_parametres import tab_parametres

# ===================== ROUTAGE ENTRE ONGLES =====================
with tabs[0]:
    tab_fichiers()

with tabs[1]:
    tab_dashboard()

with tabs[2]:
    tab_analyses()

with tabs[3]:
    tab_ajouter()

with tabs[4]:
    tab_gestion()

with tabs[5]:
    tab_compta()

with tabs[6]:
    tab_escrow()

with tabs[7]:
    tab_parametres()

# ===================== PIED DE PAGE =====================
st.markdown("---")
st.caption("Visa Manager © 2025 | Application Streamlit Cloud optimisée par ChatGPT")
