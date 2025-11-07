# -*- coding: utf-8 -*-
import streamlit as st, pandas as pd
from io import BytesIO
import escrow_manager as esc

st.set_page_config(page_title="⚙️ Paramètres", page_icon="⚙️", layout="wide")

clients, escrow = esc.load_all()

st.header("⚙️ Paramètres")
st.subheader("📥 Exporter")

c1,c2 = st.columns(2)
with c1:
    buf1 = BytesIO()
    with pd.ExcelWriter(buf1, engine="openpyxl") as w:
        clients.to_excel(w, index=False, sheet_name="Clients")
    st.download_button("📥 Télécharger Clients.xlsx", data=buf1.getvalue(),
                       file_name="Clients_export.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
with c2:
    buf2 = BytesIO()
    with pd.ExcelWriter(buf2, engine="openpyxl") as w:
        escrow.to_excel(w, index=False, sheet_name="Escrow")
    st.download_button("📥 Télécharger Escrow.xlsx", data=buf2.getvalue(),
                       file_name="Escrow_export.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

st.markdown("---")
st.caption("Visa Manager — paramètres")
