# -*- coding: utf-8 -*-
import streamlit as st, pandas as pd, datetime as dt
from pathlib import Path
import escrow_manager as esc

st.set_page_config(page_title="✏️ / 🗑️ Gestion", page_icon="✏️", layout="wide")
EXCEL_FILE = "Clients BL.xlsx"

clients, escrow = esc.load_all()

st.header("✏️ / 🗑️ Gestion")
st.dataframe(clients, use_container_width=True, height=320)
st.markdown("---")
st.subheader("Modifier un dossier")
colA,colB = st.columns([1,2])
target = colA.text_input("Dossier N à modifier")
sent2  = colB.checkbox("Dossier envoyé ?")
dsend2 = colB.date_input("Date d'envoi", dt.date.today())
esc2   = colB.checkbox("Mettre Escrow ?")

if st.button("Enregistrer la modification"):
    idx = clients.index[clients["Dossier N"].astype(str) == str(target)]
    if len(idx):
        i = idx[0]
        clients.at[i,"Dossier envoyé"] = 1 if sent2 else 0
        clients.at[i,"Date envoi"] = pd.to_datetime(dsend2) if sent2 else ""
        clients.at[i,"Escrow"] = 1 if esc2 else 0
        escrow, added = esc.sync_escrow_from_clients(clients, escrow)
        esc.save_clients_and_escrow(clients, escrow, Path(EXCEL_FILE))
        st.success("✅ Dossier modifié.")
        if added: st.info(f"Escrow : {added} ligne(s) ajoutée(s).")
    else:
        st.warning("Dossier introuvable.")
