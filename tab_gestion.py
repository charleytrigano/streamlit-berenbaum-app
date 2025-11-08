import streamlit as st
import pandas as pd
import io
from datetime import date, datetime

# ===================== Utils =====================

def to_float(x) -> float:
    try:
        s = str(x).replace("\u00A0", " ").replace(",", ".").strip()
        if s == "" or s.lower() in {"nan", "none", "null"}:
            return 0.0
        return float(s)
    except Exception:
        return 0.0

def safe_date(x) -> date:
    if x is None:
        return date.today()
    try:
        if isinstance(x, date) and not isinstance(x, datetime):
            return x
        if isinstance(x, datetime):
            return x.date()
        parsed = pd.to_datetime(x, errors="coerce")
        return date.today() if pd.isna(parsed) else parsed.date()
    except Exception:
        return date.today()

def ensure_escrow_sheet(data: dict) -> pd.DataFrame:
    if "Escrow" not in data or not isinstance(data["Escrow"], pd.DataFrame):
        data["Escrow"] = pd.DataFrame(
            columns=["Dossier N", "Nom", "Montant", "Date envoi", "État", "Date réclamation", "Commentaires"]
        )
    return data["Escrow"]

# ===================== Onglet =====================

def tab_gestion():
    """Gestion des dossiers + Escrow automatique (Acompte1>0 & Honoraires=0)."""

    st.header("✏️ / 🗑️ Gestion des dossiers")

    # Données chargées ?
    if "data_xlsx" not in st.session_state or not st.session_state["data_xlsx"]:
        st.warning("⚠️ Aucune donnée disponible. Charge d'abord le fichier via 📄 Fichiers.")
        return

    data = st.session_state["data_xlsx"]

    # Feuille Clients
    if "Clients" not in data or not isinstance(data["Clients"], pd.DataFrame):
        st.error("❌ Feuille 'Clients' absente.")
        return

    df_clients = data["Clients"].copy()
    df_escrow = ensure_escrow_sheet(data).copy()

    if df_clients.empty:
        st.info("Aucun dossier client enregistré.")
        return

    # Sélecteur de dossier
    dossiers = df_clients["Dossier N"].astype(str).tolist()
    selected = st.selectbox("Sélectionnez un dossier :", [""] + dossiers, key="gestion_dossier_select")
    if not selected:
        st.stop()

    row = df_clients[df_clients["Dossier N"].astype(str) == selected].iloc[0].copy()

    # Valeurs d'entrée (on lit d'abord depuis le fichier)
    nom_val = str(row.get("Nom", ""))
    hono_val = to_float(row.get("Montant honoraires (US $)", 0))
    ac1_val = to_float(row.get("Acompte 1", 0))
    date_ac1_val = safe_date(row.get("Date Acompte 1", ""))
    escrow_file = str(row.get("Escrow", "")).strip().lower() in {"oui", "true", "1", "x"}

    # Formulaire (les number_input renvoient les valeurs "finales" à utiliser)
    c1, c2 = st.columns([2,1])
    with c1:
        nom_val = st.text_input("Nom du client", value=nom_val, key="gestion_nom")
        commentaires = st.text_area("Commentaires", value=str(row.get("Commentaires", "")), key="gestion_comment")
    with c2:
        hono_val = st.number_input("Montant honoraires (US $)", min_value=0.0, value=hono_val, step=50.0, key="gestion_hono")
        ac1_val  = st.number_input("Acompte 1", min_value=0.0, value=ac1_val,  step=50.0, key="gestion_ac1")
        date_ac1_val = st.date_input("Date Acompte 1", value=date_ac1_val, key="gestion_date_ac1")

    # ⚙️ Calcul de la condition automatique APRÈS lecture des inputs
    condition_escrow = (ac1_val > 0.0) and (hono_val == 0.0)

    # La case se coche automatiquement si condition vraie, mais reste modifiable par l'utilisateur
    escrow_val = st.checkbox(
        "Escrow ?",
        value=(escrow_file or condition_escrow),
        key="gestion_escrow_chk"
    )

    st.markdown("---")
    colA, colB, colC = st.columns(3)

    # ---------- Enregistrer ----------
    with colA:
        if st.button("💾 Enregistrer les modifications", type="primary", key="gestion_save_btn"):
            # Mise à jour ligne Clients
            idx = df_clients.index[df_clients["Dossier N"].astype(str) == selected][0]
            df_clients.at[idx, "Nom"] = nom_val
            df_clients.at[idx, "Montant honoraires (US $)"] = hono_val
            df_clients.at[idx, "Acompte 1"] = ac1_val
            df_clients.at[idx, "Date Acompte 1"] = date_ac1_val
            df_clients.at[idx, "Escrow"] = "Oui" if escrow_val else "Non"
            df_clients.at[idx, "Commentaires"] = commentaires

            # Décision finale : soit la case est cochée, soit la condition est vraie
            must_add_to_escrow = escrow_val or condition_escrow

            # Ajout/MAJ Escrow
            in_escrow = selected in df_escrow["Dossier N"].astype(str).values
            if must_add_to_escrow:
                if in_escrow:
                    # Met à jour la ligne existante (montant / date / nom / commentaires)
                    eid = df_escrow.index[df_escrow["Dossier N"].astype(str) == selected][0]
                    df_escrow.at[eid, "Nom"] = nom_val
                    df_escrow.at[eid, "Montant"] = ac1_val
                    df_escrow.at[eid, "Date envoi"] = date_ac1_val
                    df_escrow.at[eid, "Commentaires"] = commentaires
                else:
                    # Ajoute une nouvelle ligne
                    df_escrow = pd.concat([
                        df_escrow,
                        pd.DataFrame([{
                            "Dossier N": selected,
                            "Nom": nom_val,
                            "Montant": ac1_val,
                            "Date envoi": date_ac1_val,
                            "État": "En attente",
                            "Date réclamation": "",
                            "Commentaires": commentaires,
                        }])
                    ], ignore_index=True)
                st.success(f"✅ Dossier {selected} présent dans Escrow (auto ou manuel).")
            else:
                # Si on ne doit pas être en Escrow mais qu'une ligne existe déjà, on la laisse (historique).
                st.info("💾 Modifications enregistrées.")

            # Sauvegarde en session et bouton de téléchargement
            st.session_state["data_xlsx"]["Clients"] = df_clients
            st.session_state["data_xlsx"]["Escrow"] = df_escrow

            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine="openpyxl") as w:
                for sheet_name, df_sheet in st.session_state["data_xlsx"].items():
                    df_sheet.to_excel(w, index=False, sheet_name=sheet_name)
            buf.seek(0)
            st.download_button(
                "⬇️ Télécharger Clients BL (mis à jour)",
                data=buf,
                file_name="Clients BL.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="gestion_dl_btn"
            )

            st.rerun()  # <= remplace experimental_rerun

    # ---------- Supprimer ----------
    with colB:
        if st.button("🗑️ Supprimer le dossier", key="gestion_del_btn"):
            df_clients = df_clients[df_clients["Dossier N"].astype(str) != selected]
            st.session_state["data_xlsx"]["Clients"] = df_clients
            st.success(f"🗑️ Dossier {selected} supprimé.")
            st.rerun()

    with colC:
        st.info("💡 La case Escrow se coche automatiquement si Acompte 1 > 0 et Honoraires = 0. Vous pouvez la modifier manuellement.")
