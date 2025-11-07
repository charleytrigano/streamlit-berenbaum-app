# -*- coding: utf-8 -*-
import streamlit as st, pandas as pd
import escrow_manager as esc

st.set_page_config(page_title="📈 Analyses", page_icon="📈", layout="wide")

clients, _ = esc.load_all()
st.header("📈 Analyses")

if clients.empty:
    st.info("Chargez vos données pour visualiser les analyses.")
else:
    df_ = clients.copy()
    if "Date" in df_.columns:
        df_["Date"] = pd.to_datetime(df_["Date"], errors="coerce")
        df_["_year_"]  = df_["Date"].dt.year
        df_["_month_"] = df_["Date"].dt.month
        monto = "Montant total" if "Montant total" in df_.columns else ("Montant" if "Montant" in df_.columns else None)
        if monto:
            # ✅ parenthèse corrigée
            pivot = df_.groupby([df_["_year_"], df_["_month_"]])[monto].sum().unstack(fill_value=0)
            st.bar_chart(pivot)
        else:
            st.info("Aucune colonne de montant détectée (‘Montant total’ ou ‘Montant’).")
    else:
        st.info("Colonne ‘Date’ absente.")
