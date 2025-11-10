import streamlit as st
from common_data import ensure_loaded
from tab_fichiers import tab_fichiers
from tab_gestion import tab_gestion
from tab_escrow import tab_escrow
# Importe tes autres onglets existants :
# from tab_dashboard import tab_dashboard
# from tab_analyses  import tab_analyses
# from tab_compta    import tab_compta
from tab_parametres import tab_parametres

st.set_page_config(page_title="Visa Manager", layout="wide")

# Pré-charge le fichier (si dispo) pour éviter les surprises dans les onglets
ensure_loaded("Clients BL.xlsx")

tabs = st.tabs([
    "📄 Fichiers",
    "✏️ / 🗑️ Gestion",
    "🛡️ Escrow",
    "⚙️ Paramètres",
    # "📊 Dashboard",
    # "📈 Analyses",
    # "💳 Compta Client",
])

with tabs[0]:
    tab_fichiers()

with tabs[1]:
    tab_gestion()

with tabs[2]:
    tab_escrow()

with tabs[3]:
    tab_parametres()

# with tabs[4]:
#     tab_dashboard()
# with tabs[5]:
#     tab_analyses()
# with tabs[6]:
#     tab_compta()

