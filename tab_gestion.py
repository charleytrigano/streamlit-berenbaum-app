import streamlit as st
import pandas as pd
from datetime import datetime

EXCEL_FILE = "Clients BL.xlsx"

def save_to_excel(data_dict):
    """Sauvegarde les feuilles Excel après modification ou suppression."""
    try:
        with pd.ExcelWriter(EXCEL_FILE, engine="openpyxl", mode="w") as writer:
            for sheet_name, df in data_dict.items():
                df.to_excel(writer, index=False, sheet_name=sheet_name)
        st.success("💾 Modifications enregistrées avec succès.")
        return True
    except Exception as e:
        st.error(f"Erreur lors de la sauvegarde : {e}")
        return False


def tab_gestion():
    """Onglet pour modifier ou supprimer un dossier client."""
    st.header("✏️ / 🗑️ Gestion des dossiers clients")

    if "data_xlsx" not in st.session_state or not st.session_state["data_xlsx"]:
        st.warning("⚠️ Aucune donnée chargée. Veuillez importer votre fichier Excel via l’onglet 📄 Fichiers.")
        return

    data = st.session_state["data_xlsx"]
    df_clients = data.get("Clients", pd.DataFrame())
    df_escrow = data.get("Escrow", pd.DataFrame())

    if df_clients.empty:
        st.info("Aucun dossier client trouvé dans la base.")
        return

    # Sélection du client
    client_list = df_clients["Nom"].dropna().unique().tolist()
    selected_client = st.selectbox("👤 Sélectionnez un client à modifier ou supprimer :", client_list)

    if not selected_client:
        st.info("Sélectionnez un client pour continuer.")
        return

    client_data = df_clients[df_clients["Nom"] == selected_client].iloc[0]

    with st.form("modif_dossier"):
        st.subheader(f"✏️ Modification du dossier : {selected_client}")

        col1, col2 = st.columns(2)
        visa = col1.text_input("🎟️ Type de visa", value=str(client_data.get("Type visa", "")))
        honoraires = col2.number_input("💰 Montant honoraires (US $)", min_value=0.0, step=100.0, value=float(client_data.get("Montant honoraires (US $)", 0.0)))

        col3, col4 = st.columns(2)
        autres_frais = col3.number_input("💼 Autres frais (US $)", min_value=0.0, step=100.0, value=float(client_data.get("Autres frais (US $)", 0.0)))
        acompte1 = col4.number_input("Acompte 1", min_value=0.0, step=50.0, value=float(client_data.get("Acompte 1", 0.0)))

        col5, col6 = st.columns(2)
        acompte2 = col5.number_input("Acompte 2", min_value=0.0, step=50.0, value=float(client_data.get("Acompte 2", 0.0)))
        acompte3 = col6.number_input("Acompte 3", min_value=0.0, step=50.0, value=float(client_data.get("Acompte 3", 0.0)))

        col7, col8 = st.columns(2)
        acompte4 = col7.number_input("Acompte 4", min_value=0.0, step=50.0, value=float(client_data.get("Acompte 4", 0.0)))
        escrow = st.checkbox("🛡️ Escrow", value=(selected_client in df_escrow["Nom"].values))

        submitted = st.form_submit_button("💾 Enregistrer les modifications")

        if submitted:
            montant_facture = honoraires + autres_frais
            total_paye = acompte1 + acompte2 + acompte3 + acompte4
            solde = montant_facture - total_paye

            df_clients.loc[df_clients["Nom"] == selected_client, [
                "Type visa",
                "Montant honoraires (US $)",
                "Autres frais (US $)",
                "Acompte 1", "Acompte 2", "Acompte 3", "Acompte 4",
                "Montant facturé", "Total payé", "Solde restant"
            ]] = [visa, honoraires, autres_frais, acompte1, acompte2, acompte3, acompte4, montant_facture, total_paye, solde]

            # Gestion Escrow
            if escrow:
                if selected_client not in df_escrow["Nom"].values:
                    escrow_row = {
                        "Nom": selected_client,
                        "Date création": datetime.now().strftime("%d/%m/%Y"),
                        "Montant": solde,
                        "État": "À réclamer",
                    }
                    df_escrow = pd.concat([df_escrow, pd.DataFrame([escrow_row])], ignore_index=True)
            else:
                df_escrow = df_escrow[df_escrow["Nom"] != selected_client]

            data["Clients"] = df_clients
            data["Escrow"] = df_escrow

            if save_to_excel(data):
                st.session_state["data_xlsx"] = data
                st.success("✅ Modifications enregistrées avec succès.")
                st.experimental_rerun()

    st.markdown("---")
    st.subheader("🗑️ Suppression du dossier")

    if st.button(f"❌ Supprimer le dossier {selected_client}"):
        df_clients = df_clients[df_clients["Nom"] != selected_client]
        df_escrow = df_escrow[df_escrow["Nom"] != selected_client]

        data["Clients"] = df_clients
        data["Escrow"] = df_escrow

        if save_to_excel(data):
            st.session_state["data_xlsx"] = data
            st.warning(f"🗑️ Dossier supprimé : {selected_client}")
            st.experimental_rerun()
