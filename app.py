# -*- coding: utf-8 -*-
import streamlit as st
import importlib

st.set_page_config(page_title="Visa Manager", page_icon="🗂️", layout="wide")
st.title("🗂️ Visa Manager")

# --- Définition des onglets principaux ---
tabs = st.tabs([
    "📄 Fichiers",
    "📊 Dashboard",
    "📈 Analyses",
    "➕ Ajouter",
    "✏️ / 🗑️ Gestion",
    "💳 Compta Client",
    "🛡️ Escrow",
    "⚙️ Paramètres"
])

# --- Correspondance onglet <-> module Python ---
modules = [
    "tab_fichiers",
    "tab_dashboard",
    "tab_analyses",
    "tab_ajouter",
    "tab_gestion",
    "tab_compta",
    "tab_escrow",
    "tab_parametres"
]

# --- Chargement dynamique des modules ---
for tab, module_name in zip(tabs, modules):
    with tab:
        try:
            mod = importlib.import_module(module_name)
            if hasattr(mod, "main"):
                mod.main()
            else:
                st.warning(f"⚠️ Le module `{module_name}` n’a pas de fonction main().")
        except Exception as e:
            st.error(f"Erreur lors du chargement du module `{module_name}` : {e}")
