import streamlit as st
import pandas as pd
import os

DATA_PATH = r"C:\Users\charl\Mon Drive\streamlit-berenbaum-app\Clients BL.xlsx"

def ensure_loaded():
    try:
        df_clients = pd.read_excel(DATA_PATH, sheet_name="Clients")
        st.write("Colonnes :", df_clients.columns.tolist())
        st.write("Aperçu des 5 premières lignes :", df_clients.head())
        if df_clients.empty:
            st.warning("Le fichier Excel est vide.")
            return None
    except Exception as e:
        st.error(f"Erreur lors du chargement Excel : {e}")
        return None
    return {"Clients": df_clients}
