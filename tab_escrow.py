import streamlit as st
import pandas as pd
from common_data import ensure_loaded, save_all

FILENAME = "Clients BL.xlsx"

def _fmt_money(x):
    try:
        v = float(x)
        return f"{v:,.2f} $".replace(",", " ").replace(".", ",")
    except:
        return x

def tab_escrow():
    st.title("🛡️ Escrow")

    data = ensure_loaded(FILENAME)
    df = data.get("Escrow", pd.DataFrame(columns=["Dossier N","Nom","Montant","Date envoi","Etat","Date réclamation"]))

    n = len(df)
    total = float(df["Montant"].fillna(0).sum()) if not df.empty and "Montant" in df else 0.0

    k1,k2 = st.columns(2)
    k1.metric("Dossiers en Escrow", f"{n}")
    k2.metric("Montant total", f"{total:,.2f} $".replace(",", " ").replace(".", ","))

    if df.empty:
        st.info("Aucun dossier en Escrow pour le moment.")
        return

    show = df.copy()
    if "Montant" in show:
        show["Montant"] = show["Montant"].apply(_fmt_money)

    st.dataframe(show, use_container_width=True)

    st.markdown("### 📝 Marquer un dossier comme réclamé")
    num = st.text_input("Dossier N")
    if st.button("✅ Marquer réclamé"):
        if num:
            idx = df[df["Dossier N"].astype(str)==str(num)].index
            if len(idx)>0:
                df.loc[idx, "Etat"] = "Réclamé"
                df.loc[idx, "Date réclamation"] = pd.Timestamp.today().date()
                data["Escrow"] = df
                st.session_state["data_xlsx"] = data
                save_all(FILENAME)
                st.success(f"Dossier {num} marqué comme réclamé.")
                st.rerun()
            else:
                st.warning("Numéro non trouvé.")
        else:
            st.warning("Renseigne un numéro de dossier.")
