import streamlit as st
import pandas as pd

def main():
    st.header("➕ Ajouter un dossier")

    df = st.session_state.get("clients_df", pd.DataFrame())

    nom = st.text_input("Nom du client")
    montant = st.number_input("Montant", min_value=0.0, step=100.0)
    escrow = st.checkbox("Mettre en Escrow")

    if st.button("✅ Ajouter"):
        if not nom:
            st.warning("Veuillez renseigner le nom du client.")
            return
        new_row = {"Nom": nom, "Montant": montant, "Escrow": escrow}
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        st.session_state["clients_df"] = df
        st.success(f"Dossier ajouté pour {nom}.")
