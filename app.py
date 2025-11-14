import plotly.express as px
import streamlit as st
from common_data import ensure_loaded, MAIN_FILE

st.set_page_config(page_title="Visa Manager", page_icon="🧾", layout="wide")

st.session_state.setdefault("data_xlsx", ensure_loaded(MAIN_FILE))

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

from tab_fichiers import tab_fichiers
from tab_dashboard import tab_dashboard
from tab_analyses import tab_analyses
from tab_ajouter import tab_ajouter
from tab_gestion import tab_gestion
from tab_compta import tab_compta
from tab_escrow import tab_escrow
from tab_parametres import tab_parametres

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
