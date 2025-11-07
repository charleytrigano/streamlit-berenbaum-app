# -*- coding: utf-8 -*-
import streamlit as st, pandas as pd, datetime as dt
from pathlib import Path
import escrow_manager as esc

st.set_page_config(page_title="➕ Ajouter", page_icon="➕", layout="wide")
EXCEL_FILE = "Clients BL.xlsx"

clients, escrow = esc.load_all()

st.header("➕ Ajouter un dossier")
with st.form("add_form"):
    col1,col2,col3 = st.columns(3)
    dnum = col1.text_input("Dossier N")
    nom  = col2.text_input("Nom")
    dte  = col3.date_input("Date", dt.date.today())
    col4,col5 = st.columns(2)
    mt_total = col4.text_input("Montant total (€)", value="0")
    ac1      = col5.text_input("Acompte 1 (€)", value="0")
    col6,col7 = st.columns(2)
    sent  = col6.checkbox("Dossier envoyé ?")
    dsend = col7.date_input("Date envoi", dt.date.today())
    escf = st.checkbox("Escrow ?")
    ok = st.form_submit_button("Ajouter")

if ok:
    row = {
        "Dossier N": dnum, "Nom": nom, "Date": pd.to_datetime(dte),
        "Montant total": mt_total, "Acompte 1": ac1,
        "Dossier envoyé": 1 if sent else 0,
        "Date envoi": pd.to_datetime(dsend) if sent else "",
        "Escrow": 1 if escf else 0
    }
    clients = pd.concat([clients, pd.DataFrame([row])], ignore_index=True)
    escrow, added = esc.sync_escrow_from_clients(clients, escrow)
    esc.save_clients_and_escrow(clients, escrow, Path(EXCEL_FILE))
    st.success("✅ Dossier ajouté.")
    if added: st.info(f"Escrow : {added} ligne(s) ajoutée(s).")
