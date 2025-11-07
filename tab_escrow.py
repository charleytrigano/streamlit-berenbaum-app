# -*- coding: utf-8 -*-
import streamlit as st, pandas as pd
from pathlib import Path
import escrow_manager as esc

st.set_page_config(page_title="🛡️ Escrow", page_icon="🛡️", layout="wide")
EXCEL_FILE = "Clients BL.xlsx"

clients, escrow = esc.load_all(Path(EXCEL_FILE))

st.header("🛡️ Escrow")
escrow, added = esc.sync_escrow_from_clients(clients, escrow)
if added:
    esc.save_clients_and_escrow(clients, escrow, Path(EXCEL_FILE))
    st.info(f"Synchronisation : {added} ligne(s) ajoutée(s).")

pend = esc.pending(escrow)
if not pend.empty:
    st.error(f"⚠️ {len(pend)} dossier(s) à réclamer")
else:
    st.success("✅ Aucun Escrow à réclamer.")

cols_show = ["Dossier N","Nom","Date envoi","Montant"]

st.subheader("À réclamer")
v = pend.copy()
for c in cols_show:
    if c not in v.columns: v[c] = ""
st.dataframe(v[cols_show], use_container_width=True, height=260)

st.subheader("Réclamés")
r = esc.claimed(escrow)
if not r.empty:
    rv = r.copy()
    for c in cols_show:
        if c not in rv.columns: rv[c] = ""
    st.dataframe(rv[cols_show], use_container_width=True, height=260)
else:
    st.info("Aucun dossier réclamé.")

st.markdown("---")
st.subheader("Marquer un dossier comme réclamé")
num = st.text_input("Numéro de dossier")
if st.button("✅ Marquer comme réclamé"):
    escrow, ok = esc.mark_escrow_reclaimed(escrow, num)
    if ok:
        esc.save_clients_and_escrow(clients, escrow, Path(EXCEL_FILE))
        st.success(f"Dossier {num} marqué comme réclamé.")
    else:
        st.warning("Numéro de dossier introuvable.")
