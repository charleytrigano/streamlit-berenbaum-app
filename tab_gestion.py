import streamlit as st
import pandas as pd
import io
import dropbox
from datetime import date, datetime

def safe_date(val):
    """Convertit proprement n’importe quelle valeur en date."""
    if pd.isna(val) or val is None:
        return date.today()
    try:
        if isinstance(val, date):
            return val
        if isinstance(val, datetime):
            return val.date()
        if isinstance(val, str) and val.strip():
            parsed = pd.to_datetime(val, errors="coerce")
            if pd.notna(parsed):
                return parsed.date()
    except Exception:
        pass
    return date.today()

def to_float(val):
    """Convertit proprement en float pour éviter les 'nan', strings, etc."""
    try:
        return float(str(val).replace(",", ".").strip()) if str(val).strip() not in ["", "nan", "NaN", "None"] else 0.0
    except Exception:
        return 0.0


def tab_gestion():
    """Onglet Gestion — modification/suppression des dossiers clients, et Escrow automatique."""

    st.header("✏️ / 🗑️ Gestion des dossiers")

    if "data_xlsx" not in st.session_state or not st.session_state["data_xlsx"]:
        st.warning("⚠️ Aucune donnée disponible. Chargez d'abord le fichier Excel via l'onglet 📄 Fichiers.")
        return

    data = st.session_state["data_xlsx"]

    if "Clients" not in data:
        st.error("❌ Feuille 'Clients' manquante dans le fichier Excel.")
        return

    df_clients = data["Clients"].copy()
    df_escrow = data.get("Escrow", pd.DataFrame(columns=[
        "Dossier N", "Nom", "Montant", "Date envoi", "État", "Date réclamation", "Commentaires"
    ]))

    if df_clients.empty:
        st.info("Aucun dossier client enregistré.")
        return

    dossier_list = df_clients["Dossier N"].astype(str).tolist()
    selected_dossier = st.selectbox("Sélectionnez un dossier :", options=[""] + dossier_list, key="gestion_dossier_select")
    if not selected_dossier:
        st.stop()

    dossier_data = df_clients[df_clients["Dossier N"].astype(str) == selected_dossier].iloc[0].copy()

    st.markdown("### 🔧 Modifier le dossier sélectionné")

    date_parsed = safe_date(dossier_data.get("Date Acompte 1", ""))
    montant = to_float(dossier_data.get("Montant honoraires (US $)", 0))
    acompte = to_float(dossier_data.get("Acompte 1", 0))

    nom = st.text_input("Nom du client", value=str(dossier_data.get("Nom", "")), key="gestion_nom")
    montant = st.number_input("Montant honoraires (US $)", min_value=0.0, value=montant, step=50.0, key="gestion_montant")
    acompte = st.number_input("Acompte 1", min_value=0.0, value=acompte, step=50.0, key="gestion_acompte")
    date_acompte = st.date_input("Date Acompte 1", value=date_parsed, key="gestion_date_acompte")
    escrow = st.checkbox("Escrow ?", value=bool(dossier_data.get("Escrow", False)), key="gestion_escrow")
    commentaire = st.text_area("Commentaires", value=dossier_data.get("Commentaires", ""), key="gestion_commentaire")

    st.markdown("---")
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("💾 Enregistrer les modifications", key="gestion_save_btn"):
            idx = df_clients.index[df_clients["Dossier N"].astype(str) == selected_dossier][0]
            df_clients.at[idx, "Nom"] = nom
            df_clients.at[idx, "Montant honoraires (US $)"] = montant
            df_clients.at[idx, "Acompte 1"] = acompte
            df_clients.at[idx, "Date Acompte 1"] = date_acompte
            df_clients.at[idx, "Escrow"] = escrow
            df_clients.at[idx, "Commentaires"] = commentaire

            # === CAS 1 : ESCROW coche OU acompte sans honoraire ===
            deja_escrow = selected_dossier in df_escrow["Dossier N"].astype(str).values
            montant_vide = (montant == 0 or pd.isna(montant))
            acompte_valide = (acompte > 0)

            if (escrow or (acompte_valide and montant_vide)) and not deja_escrow:
                new_row = {
                    "Dossier N": selected_dossier,
                    "Nom": nom,
                    "Montant": acompte,
                    "Date envoi": date_acompte,
                    "État": "En attente",
                    "Date réclamation": "",
                    "Commentaires": commentaire,
                }
                df_escrow = pd.concat([df_escrow, pd.DataFrame([new_row])], ignore_index=True)
                st.success(f"✅ Dossier {selected_dossier} ajouté automatiquement dans Escrow.")
            elif deja_escrow:
                st.info(f"ℹ️ Dossier {selected_dossier} déjà présent dans Escrow.")
            else:
                st.info("Aucun ajout Escrow requis.")

            # === CAS 2 : Vérification globale des autres dossiers ===
            added = []
            for _, row in df_clients.iterrows():
                acompte_check = to_float(row.get("Acompte 1", 0))
                montant_check = to_float(row.get("Montant honoraires (US $)", 0))
                dossier_num = str(row.get("Dossier N", ""))
                if acompte_check > 0 and montant_check == 0:
                    if dossier_num not in df_escrow["Dossier N"].astype(str).values:
                        df_escrow = pd.concat([df_escrow, pd.DataFrame([{
                            "Dossier N": dossier_num,
                            "Nom": row.get("Nom", ""),
                            "Montant": acompte_check,
                            "Date envoi": safe_date(row.get("Date Acompte 1", date.today())),
                            "État": "En attente",
                            "Date réclamation": "",
                            "Commentaires": row.get("Commentaires", ""),
                        }])], ignore_index=True)
                        added.append(dossier_num)

            if added:
                st.success(f"✅ {len(added)} dossiers ajoutés automatiquement à Escrow : {', '.join(added)}")

            st.session_state["data_xlsx"]["Clients"] = df_clients
            st.session_state["data_xlsx"]["Escrow"] = df_escrow

            st.success("💾 Modifications enregistrées localement.")

            # === SAUVEGARDE ===
            save_mode = st.radio("Choisissez où sauvegarder :", ["💻 Local", "☁️ Dropbox"],
                                 horizontal=True, key="gestion_save_choice")

            if save_mode == "💻 Local":
                with io.BytesIO() as buffer:
                    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                        for sheet, df in st.session_state["data_xlsx"].items():
                            df.to_excel(writer, index=False, sheet_name=sheet)
                    buffer.seek(0)
                    st.download_button("⬇️ Télécharger le fichier Excel mis à jour", buffer,
                                       "Clients BL.xlsx",
                                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                       key="gestion_dl_btn")

            elif save_mode == "☁️ Dropbox":
                try:
                    token = st.secrets["DROPBOX_TOKEN"]
                    folder = st.secrets.get("DROPBOX_FOLDER", "/")
                    dbx = dropbox.Dropbox(token)
                    with io.BytesIO() as buffer:
                        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                            for sheet, df in st.session_state["data_xlsx"].items():
                                df.to_excel(writer, index=False, sheet_name=sheet)
                        buffer.seek(0)
                        dbx.files_upload(buffer.read(), f"{folder}/Clients BL.xlsx",
                                         mode=dropbox.files.WriteMode("overwrite"))
                    st.success("✅ Fichier sauvegardé sur Dropbox.")
                except Exception as e:
                    st.warning(f"⚠️ Sauvegarde Dropbox échouée : {e}")

    with col2:
        if st.button("🗑️ Supprimer le dossier", key="gestion_delete_btn"):
            df_clients = df_clients[df_clients["Dossier N"].astype(str) != selected_dossier]
            st.session_state["data_xlsx"]["Clients"] = df_clients
            st.success(f"🗑️ Dossier {selected_dossier} supprimé.")
            st.experimental_rerun()

    with col3:
        st.info("💡 Les sauvegardes peuvent être faites localement ou sur Dropbox.")
