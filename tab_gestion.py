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
    st.header("✏️ / 🗑️ Gestion des dossiers")

    if "data_xlsx" not in st.session_state or not st.session_state["data_xlsx"]:
        st.warning("⚠️ Aucune donnée disponible. Chargez d'abord le fichier Excel via 📄 Fichiers.")
        return

    data = st.session_state["data_xlsx"]
    if "Clients" not in data:
        st.error("❌ Feuille 'Clients' absente.")
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

    # Lecture des champs existants
    nom = st.text_input("Nom du client", row.get("Nom", ""))
    montant = to_float(row.get("Montant honoraires (US $)", 0))
    acompte1 = to_float(row.get("Acompte 1", 0))
    date_acompte1 = safe_date(row.get("Date Acompte 1", date.today()))

    # ⚙️ Coche automatique de la case Escrow
    condition_escrow = acompte1 > 0 and montant == 0
    escrow_auto = str(row.get("Escrow", "")).strip().lower() in ["oui", "true", "1", "x"]
    escrow_value = escrow_auto or condition_escrow
    escrow = st.checkbox("Escrow ?", value=escrow_value)

    commentaires = st.text_area("Commentaires", row.get("Commentaires", ""))

    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        if st.button("💾 Enregistrer les modifications", type="primary"):
            idx = df_clients.index[df_clients["Dossier N"].astype(str) == selected][0]
            df_clients.at[idx, "Nom"] = nom
            df_clients.at[idx, "Montant honoraires (US $)"] = montant
            df_clients.at[idx, "Acompte 1"] = acompte1
            df_clients.at[idx, "Date Acompte 1"] = date_acompte1
            df_clients.at[idx, "Escrow"] = "Oui" if escrow else "Non"
            df_clients.at[idx, "Commentaires"] = commentaires

            # Détection ajout escrow
            ajout_escrow = False
            deja_escrow = selected in df_escrow["Dossier N"].astype(str).values

            if (escrow or condition_escrow) and not deja_escrow:
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
                st.success(f"✅ Dossier {selected} ajouté à Escrow.")
            elif deja_escrow:
                st.info(f"ℹ️ Dossier {selected} déjà présent dans Escrow.")
            else:
                st.info("Aucun ajout Escrow requis (aucune condition remplie).")

            # Sauvegarde
            st.session_state["data_xlsx"]["Clients"] = df_clients
            st.session_state["data_xlsx"]["Escrow"] = df_escrow

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

            st.experimental_rerun()

    with col2:
        if st.button("🗑️ Supprimer le dossier"):
            df_clients = df_clients[df_clients["Dossier N"].astype(str) != selected]
            st.session_state["data_xlsx"]["Clients"] = df_clients
            st.success(f"🗑️ Dossier {selected} supprimé.")
            st.experimental_rerun()
