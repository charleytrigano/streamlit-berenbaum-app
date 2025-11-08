import streamlit as st
import pandas as pd
import io
import dropbox
from datetime import date, datetime

def to_float(x):
    try:
        if pd.isna(x) or str(x).strip().lower() in ["", "nan", "none"]:
            return 0.0
        return float(str(x).replace(",", "."))
    except Exception:
        return 0.0

def safe_date(x):
    try:
        if pd.isna(x) or str(x).strip() == "":
            return date.today()
        return pd.to_datetime(x, errors="coerce").date()
    except Exception:
        return date.today()

def tab_gestion():
    """Onglet Gestion avec Escrow automatique et sauvegarde réelle"""
    st.header("✏️ / 🗑️ Gestion des dossiers")

    # Vérification du chargement
    if "data_xlsx" not in st.session_state or not st.session_state["data_xlsx"]:
        st.warning("⚠️ Aucune donnée disponible. Chargez d'abord le fichier Excel via 📄 Fichiers.")
        return

    data = st.session_state["data_xlsx"]
    if "Clients" not in data:
        st.error("❌ La feuille 'Clients' est absente.")
        return

    df_clients = data["Clients"].copy()
    df_escrow = data.get("Escrow", pd.DataFrame(columns=["Dossier N", "Nom", "Montant", "Date envoi", "État", "Commentaires"]))

    if df_clients.empty:
        st.info("Aucun dossier client enregistré.")
        return

    dossiers = df_clients["Dossier N"].astype(str).tolist()
    selected = st.selectbox("Sélectionnez un dossier :", [""] + dossiers)
    if not selected:
        st.stop()

    row = df_clients[df_clients["Dossier N"].astype(str) == selected].iloc[0].copy()

    # Champs à modifier
    nom = st.text_input("Nom du client", row.get("Nom", ""))
    montant = st.number_input("Montant honoraires (US $)", min_value=0.0, value=to_float(row.get("Montant honoraires (US $)", 0)))
    acompte1 = st.number_input("Acompte 1", min_value=0.0, value=to_float(row.get("Acompte 1", 0)))
    date_acompte1 = st.date_input("Date Acompte 1", value=safe_date(row.get("Date Acompte 1", date.today())))
    escrow = st.checkbox("Escrow ?", value=str(row.get("Escrow", "")).strip().lower() in ["oui", "true", "1", "x"])
    commentaires = st.text_area("Commentaires", row.get("Commentaires", ""))

    st.markdown("---")
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("💾 Enregistrer les modifications", type="primary"):
            idx = df_clients.index[df_clients["Dossier N"].astype(str) == selected][0]
            df_clients.at[idx, "Nom"] = nom
            df_clients.at[idx, "Montant honoraires (US $)"] = montant
            df_clients.at[idx, "Acompte 1"] = acompte1
            df_clients.at[idx, "Date Acompte 1"] = date_acompte1
            df_clients.at[idx, "Escrow"] = "Oui" if escrow else "Non"
            df_clients.at[idx, "Commentaires"] = commentaires

            # 🔹 Détection Escrow automatique
            ajout_escrow = False
            deja_escrow = selected in df_escrow["Dossier N"].astype(str).values

            if (escrow or (acompte1 > 0 and montant == 0)) and not deja_escrow:
                new_row = pd.DataFrame([{
                    "Dossier N": selected,
                    "Nom": nom,
                    "Montant": acompte1,
                    "Date envoi": date_acompte1,
                    "État": "En attente",
                    "Commentaires": commentaires,
                }])
                df_escrow = pd.concat([df_escrow, new_row], ignore_index=True)
                ajout_escrow = True

            # Mise à jour session
            st.session_state["data_xlsx"]["Clients"] = df_clients
            st.session_state["data_xlsx"]["Escrow"] = df_escrow

            # Sauvegarde locale directe (fichier mis à jour)
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                for sheet, df in st.session_state["data_xlsx"].items():
                    df.to_excel(writer, index=False, sheet_name=sheet)
            buffer.seek(0)

            st.download_button(
                label="⬇️ Télécharger Clients BL mis à jour",
                data=buffer,
                file_name="Clients BL.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

            if ajout_escrow:
                st.success(f"✅ Dossier {selected} ajouté à Escrow.")
            else:
                st.info("💾 Modifications enregistrées.")

            st.experimental_rerun()

    with col2:
        if st.button("🗑️ Supprimer le dossier"):
            df_clients = df_clients[df_clients["Dossier N"].astype(str) != selected]
            st.session_state["data_xlsx"]["Clients"] = df_clients
            st.success(f"🗑️ Dossier {selected} supprimé.")
            st.experimental_rerun()

    with col3:
        st.info("💡 Les sauvegardes peuvent être faites localement ou via Dropbox.")
