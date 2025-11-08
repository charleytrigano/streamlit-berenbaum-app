import streamlit as st
import pandas as pd
from datetime import datetime
import os

EXCEL_FILE = "Clients BL.xlsx"

def save_to_excel(data_dict):
    """Sauvegarde toutes les feuilles dans le fichier Excel."""
    try:
        with pd.ExcelWriter(EXCEL_FILE, engine="openpyxl", mode="w") as writer:
            for sheet_name, df in data_dict.items():
                df.to_excel(writer, index=False, sheet_name=sheet_name)
        st.success("💾 Données enregistrées avec succès dans le fichier Excel.")
        return True
    except Exception as e:
        st.error(f"Erreur lors de l’enregistrement : {e}")
        return False


def tab_ajouter():
    """Onglet pour ajouter un nouveau dossier client."""
    st.header("➕ Ajouter un nouveau dossier client")

    if "data_xlsx" not in st.session_state or not st.session_state["data_xlsx"]:
        st.warning("⚠️ Aucune donnée chargée. Charge le fichier Excel via l’onglet 📄 Fichiers.")
        return

    data = st.session_state["data_xlsx"]
    df_clients = data.get("Clients", pd.DataFrame())
    df_escrow = data.get("Escrow", pd.DataFrame())

    with st.form("ajouter_dossier_form"):
        col1, col2 = st.columns(2)
        nom = col1.text_input("👤 Nom du client")
        visa = col2.text_input("🎟️ Type de visa")

        col3, col4 = st.columns(2)
        honoraires = col3.number_input("💰 Montant honoraires (US $)", min_value=0.0, step=100.0)
        autres_frais = col4.number_input("💼 Autres frais (US $)", min_value=0.0, step=100.0)

        col5, col6 = st.columns(2)
        acompte1 = col5.number_input("Acompte 1", min_value=0.0, step=50.0)
        acompte2 = col6.number_input("Acompte 2", min_value=0.0, step=50.0)

        col7, col8 = st.columns(2)
        acompte3 = col7.number_input("Acompte 3", min_value=0.0, step=50.0)
        acompte4 = col8.number_input("Acompte 4", min_value=0.0, step=50.0)

        escrow = st.checkbox("🛡️ Escrow (dossier en attente de règlement via séquestre)")
        date_creation = datetime.now().strftime("%d/%m/%Y")

        submitted = st.form_submit_button("✅ Ajouter le dossier")

        if submitted:
            if not nom or not visa:
                st.warning("Veuillez renseigner au minimum le nom du client et le type de visa.")
                return

            # Calculs automatiques
            montant_total = honoraires + autres_frais
            total_paye = acompte1 + acompte2 + acompte3 + acompte4
            solde = montant_total - total_paye

            nouveau = {
                "Nom": nom,
                "Type visa": visa,
                "Date création": date_creation,
                "Montant honoraires (US $)": honoraires,
                "Autres frais (US $)": autres_frais,
                "Montant facturé": montant_total,
                "Acompte 1": acompte1,
                "Acompte 2": acompte2,
                "Acompte 3": acompte3,
                "Acompte 4": acompte4,
                "Total payé": total_paye,
                "Solde restant": solde,
                "Année": datetime.now().year,
                "Mois": datetime.now().strftime("%B"),
            }

            df_clients = pd.concat([df_clients, pd.DataFrame([nouveau])], ignore_index=True)
            data["Clients"] = df_clients

            # Gestion du cas Escrow
            if escrow:
                escrow_row = {
                    "Nom": nom,
                    "Date création": date_creation,
                    "Montant": solde,
                    "État": "À réclamer",
                }
                df_escrow = pd.concat([df_escrow, pd.DataFrame([escrow_row])], ignore_index=True)
                data["Escrow"] = df_escrow
                st.info(f"🛡️ Dossier ajouté à la liste Escrow : {nom} ({solde:,.2f} $)")

            if save_to_excel(data):
                st.session_state["data_xlsx"] = data
                st.success(f"✅ Dossier ajouté avec succès pour {nom}.")
                st.experimental_rerun()

    st.markdown("---")
    st.subheader("📋 Derniers dossiers enregistrés")
    if not df_clients.empty:
        st.dataframe(df_clients.tail(10), use_container_width=True)
    else:
        st.info("Aucun dossier dans la base actuellement.")
