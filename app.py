import streamlit as st
import pandas as pd

# Charger les fonctions principales
from common_data import ensure_loaded, MAIN_FILE

# Configuration générale de l’application
st.set_page_config(
    page_title="Visa Manager",
    page_icon="🧾",
    layout="wide"
)

# Si aucun fichier n'est encore chargé, avertir l'utilisateur
if "data_xlsx" not in st.session_state or st.session_state["data_xlsx"] is None:
    st.warning("⚠️ Fichier non chargé — veuillez l'importer via l’onglet 📄 Fichiers.")

# Définition des onglets
tabs = st.tabs([
    "📄 Fichiers",
    "📊 Dashboard",
    "📈 Analyses",
    "➕ Ajouter",
    "✏️ / 🗑️ Gestion",
    "💳 Compta Client",
    "🛡️ Escrow",
    "⚙️ Paramètres",
])

# Import des modules après création des tabs pour éviter cycles d'import
from tab_fichiers import tab_fichiers
from tab_dashboard import tab_dashboard
from tab_analyses import tab_analyses
from tab_ajouter import tab_ajouter
from tab_gestion import tab_gestion
from tab_compta import tab_compta
from tab_escrow import tab_escrow
from tab_parametres import tab_parametres

# Affichage réel des onglets
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