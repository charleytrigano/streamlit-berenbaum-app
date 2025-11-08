import streamlit as st
import pandas as pd
import io
from datetime import date, datetime

# =========================
# 🔧 UTILITAIRES
# =========================

def to_float(x):
    try:
        s = str(x).replace("\u00A0", " ").replace(",", ".").strip()
        if s == "" or s.lower() in {"nan", "none"}:
            return 0.0
        return float(s)
    except Exception:
        return 0.0

def safe_date(x):
    try:
        if pd.isna(x) or x in ["", None]:
            return date.today()
        return pd.to_datetime(x, errors="coerce").date()
    except Exception:
        return date.today()

def ensure_escrow(data):
    if "Escrow" not in data or not isinstance(data["Escrow"], pd.DataFrame):
        data["Escrow"] = pd.DataFrame(columns=["Dossier N", "Nom", "Montant", "Date envoi", "État", "Commentaires"])
    return data["Escrow"]

# =========================
# 📋 ONGLET GESTION
# =========================

def tab_gestion():
    st.header("✏️ / 🗑️ Gestion des dossiers")

    # Vérif data
    if "data_xlsx" not in st.session_state or not st.session_state["data_xlsx"]:
        st.warning("⚠️ Aucune donnée disponible. Chargez le fichier Excel via 📄 Fichiers.")
        return

    data = st.session_state["data_xlsx"]
    if "Clients" not in data:
        st.error("❌ Feuille 'Clients' absente.")
        return

    df_clients = data["Clients"].copy()
    df_escrow = ensure_escrow(data).copy()

    if df_clients.empty:
        st.info("Aucun dossier client enregistré.")
        return

    dossiers = df_clients["Dossier N"].astype(str).tolist()
    selected = st.selectbox("Sélectionnez un dossier :", [""] + dossiers)
    if not selected:
        st.stop()

    row = df_clients[df_clients["Dossier N"].astype(str) == selected].iloc[0].copy()

    # === CHAMPS ===
    nom = st.text_input("Nom du client", row.get("Nom", ""))
    montant = to_float(row.get("Montant honoraires (US $)", 0))
    acompte1 = to_float(row.get("Acompte 1", 0))
    date_acompte1 = safe_date(row.get("Date Acompte 1", date.today()))
    commentaires = st.text_area("Commentaires", row.get("Commentaires", ""))

    # === ESCROW AUTO ===
    condition_auto = acompte1 > 0 and montant == 0
    escrow_checked = str(row.get("Escrow", "")).strip().lower() in ["oui", "true", "1", "x"]
    escrow = st.checkbox("Escrow ?", value=(escrow_checked or condition_auto))

    st.markdown("---")
    c1, c2 = st.columns(2)

    # =========================
    # 💾 ENREGISTRER
    # =========================
    with c1:
        if st.button("💾 Enregistrer les modifications", type="primary"):
            idx = df_clients.index[df_clients["Dossier N"].astype(str) == selected][0]

            # Mise à jour Clients
            df_clients.at[idx, "Nom"] = nom
            df_clients.at[idx, "Montant honoraires (US $)"] = montant
            df_clients.at[idx, "Acompte 1"] = acompte1
            df_clients.at[idx, "Date Acompte 1"] = date_acompte1
            df_clients.at[idx, "Escrow"] = "Oui" if escrow else "Non"
            df_clients.at[idx, "Commentaires"] = commentaires

            # Condition d’ajout à Escrow
            must_add = escrow or condition_auto
            already = selected in df_escrow["Dossier N"].astype(str).values

            if must_add:
                if already:
                    # Mise à jour si déjà présent
                    df_escrow.loc[
                        df_escrow["Dossier N"].astype(str) == selected,
                        ["Nom", "Montant", "Date envoi", "Commentaires"]
                    ] = [nom, acompte1, date_acompte1, commentaires]
                    st.info(f"ℹ️ Dossier {selected} mis à jour dans Escrow.")
                else:
                    # Ajout nouveau
                    new_row = pd.DataFrame([{
                        "Dossier N": selected,
                        "Nom": nom,
                        "Montant": acompte1,
                        "Date envoi": date_acompte1,
                        "État": "En attente",
                        "Commentaires": commentaires
                    }])
                    df_escrow = pd.concat([df_escrow, new_row], ignore_index=True)
                    st.success(f"✅ Dossier {selected} ajouté à Escrow.")
            else:
                st.info("💾 Dossier enregistré sans ajout Escrow.")

            # === MISE À JOUR MÉMOIRE & FICHIER ===
            st.session_state["data_xlsx"]["Clients"] = df_clients
            st.session_state["data_xlsx"]["Escrow"] = df_escrow

            # Sauvegarde dans le fichier
            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine="openpyxl") as writer:
                for sheet_name, df_sheet in st.session_state["data_xlsx"].items():
                    df_sheet.to_excel(writer, index=False, sheet_name=sheet_name)
            buf.seek(0)

            st.download_button(
                "⬇️ Télécharger Clients BL mis à jour",
                data=buf,
                file_name="Clients BL.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

            # Affiche un aperçu des dernières lignes Escrow
            st.markdown("### 📘 Aperçu Escrow (dernières lignes)")
            st.dataframe(df_escrow.tail(10), use_container_width=True)

            # 🔁 Relance à la fin
            st.session_state["last_saved_dossier"] = selected
            st.rerun()

    # =========================
    # 🗑️ SUPPRIMER
    # =========================
    with c2:
        if st.button("🗑️ Supprimer le dossier"):
            df_clients = df_clients[df_clients["Dossier N"].astype(str) != selected]
            st.session_state["data_xlsx"]["Clients"] = df_clients
            st.success(f"🗑️ Dossier {selected} supprimé.")
            st.rerun()
