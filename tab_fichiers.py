# -*- coding: utf-8 -*-
import streamlit as st, pandas as pd
from pathlib import Path
import escrow_manager as esc

st.set_page_config(page_title="📄 Fichiers", page_icon="📄", layout="wide")
EXCEL_FILE = "Clients BL.xlsx"

st.header("📄 Fichiers")
st.write("Fichier de travail :", f"`{EXCEL_FILE}`")

up = st.file_uploader("Importer un .xlsx (doit contenir 'Clients' et 'Escrow')", type=["xlsx"])
if up is not None:
    try:
        xls = pd.ExcelFile(up)
        if "Clients" not in xls.sheet_names or "Escrow" not in xls.sheet_names:
            st.error(f"Le fichier doit contenir 'Clients' et 'Escrow' (vus: {xls.sheet_names})")
        else:
            clients = pd.read_excel(xls, "Clients")
            escrow  = pd.read_excel(xls, "Escrow")
            escrow, added = esc.sync_escrow_from_clients(clients, escrow)
            esc.save_clients_and_escrow(clients, escrow, Path(EXCEL_FILE))
            st.success(f"✅ Import OK. Escrow ajouté : {added} ligne(s).")
    except Exception as e:
        st.error(f"Erreur d'import: {e}")
