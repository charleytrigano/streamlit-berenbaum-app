# -*- coding: utf-8 -*-
import streamlit as st, pandas as pd
import escrow_manager as esc

st.set_page_config(page_title="📊 Dashboard", page_icon="📊", layout="wide")

clients, escrow = esc.load_all()
st.header("📊 Tableau de bord")

if clients.empty:
    st.info("Aucune donnée. Ajoutez un dossier ou chargez votre fichier Excel.")
else:
    c1,c2,c3 = st.columns(3)
    total = len(clients)
    total_mt = clients.get("Montant total", pd.Series([0]*total)).apply(esc.to_float).sum()
    total_ac1 = clients.get("Acompte 1", pd.Series([0]*total)).apply(esc.to_float).sum()
    c1.metric("Nombre de dossiers", total)
    c2.metric("Montant total", f"{total_mt:,.2f} €".replace(",", " ").replace(".", ","))
    c3.metric("Acompte 1 (total)", f"{total_ac1:,.2f} €".replace(",", " ").replace(".", ","))
    st.dataframe(clients, use_container_width=True, height=420)
