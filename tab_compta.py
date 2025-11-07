# -*- coding: utf-8 -*-
import streamlit as st, pandas as pd
import escrow_manager as esc

st.set_page_config(page_title="💳 Compta Client", page_icon="💳", layout="wide")

clients, _ = esc.load_all()
st.header("💳 Compta Client")

if clients.empty:
    st.info("Aucune donnée.")
else:
    cols = [c for c in ["Montant total","Acompte 1","Montant"] if c in clients.columns]
    if cols:
        for c in cols: clients[c] = clients[c].apply(esc.to_float)
        agg = clients.groupby("Nom")[cols].sum().reset_index()
        st.dataframe(agg, use_container_width=True, height=420)
    else:
        st.dataframe(clients, use_container_width=True, height=420)
