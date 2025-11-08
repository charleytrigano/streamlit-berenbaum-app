import streamlit as st
import pandas as pd
import io
import dropbox
from datetime import date, datetime

# -------------------- Utils robustes --------------------

def _norm(s) -> str:
    return str(s).strip()

def pick_col(df: pd.DataFrame, candidates: list[str], default_name: str, fill=None) -> str:
    """Retourne le premier nom de colonne existant (parmi les alias), sinon crée une colonne vide et la retourne."""
    cols = {_norm(c).lower(): c for c in df.columns}
    for alias in candidates:
        key = _norm(alias).lower()
        if key in cols:
            return cols[key]
    # crée la colonne si absente
    df[default_name] = fill
    return default_name

def to_float(val) -> float:
    """Convertit n'importe quoi en float; vide/nan/texte exotique -> 0.0"""
    try:
        s = str(val).replace("\u00A0", " ").replace(",", ".").strip()
        if s == "" or s.lower() in {"nan", "none", "null"}:
            return 0.0
        return float(s)
    except Exception:
        return 0.0

def safe_date(val):
    """Retourne toujours un datetime.date"""
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return date.today()
    if isinstance(val, date) and not isinstance(val, datetime):
        return val
    if isinstance(val, datetime):
        return val.date()
    try:
        parsed = pd.to_datetime(val, errors="coerce")
        if pd.isna(parsed):
            return date.today()
        return parsed.date()
    except Exception:
        return date.today()

# -------------------------------------------------------

def tab_gestion():
    """Onglet Gestion — édition des dossiers + Escrow automatique (blindé)."""
    st.header("✏️ / 🗑️ Gestion des dossiers")

    # 1) Données présentes ?
    if "data_xlsx" not in st.session_state or not st.session_state["data_xlsx"]:
        st.warning("⚠️ Aucune donnée disponible. Charge d'abord le fichier via l'onglet 📄 Fichiers.")
        return

    data = st.session_state["data_xlsx"]
    if "Clients" not in data:
        st.error("❌ Feuille 'Clients' absente.")
        return

    df_clients = data["Clients"].copy()
    # Feuille Escrow créée si absente
    df_escrow = data.get("Escrow", pd.DataFrame(columns=[
        "Dossier N", "Nom", "Montant", "Date envoi", "État", "Date réclamation", "Commentaires"
    ])).copy()

    if df_clients.empty:
        st.info("Aucun dossier client enregistré.")
        return

    # 2) Mapping de colonnes robuste (alias)
    # Dossier
    COL_DOSSIER = pick_col(df_clients,
        ["Dossier N", "Dossier", "N dossier", "Dossier No", "Dossier Nº"],
        "Dossier N", fill=""
    )
    # Nom
    COL_NOM = pick_col(df_clients,
        ["Nom", "Nom du client", "Client"],
        "Nom", fill=""
    )
    # Honoraires
    COL_HONO = pick_col(df_clients,
        ["Montant honoraires (US $)", "Montant honoraires (US$)", "Montant honoraires (USD)",
         "Montant honoraires", "Honoraires"],
        "Montant honoraires (US $)", fill=0.0
    )
    # Acompte 1
    COL_AC1 = pick_col(df_clients,
        ["Acompte 1", "Acompte1", "Acpt 1"],
        "Acompte 1", fill=0.0
    )
    # Date acompte 1
    COL_DATE_AC1 = pick_col(df_clients,
        ["Date Acompte 1", "Date acompte 1", "Acompte 1 Date", "Date Acompte1"],
        "Date Acompte 1", fill=""
    )
    # Escrow (bool/texte)
    COL_ESCROW = pick_col(df_clients,
        ["Escrow"],
        "Escrow", fill=""
    )
    # Commentaires
    COL_COMMENT = pick_col(df_clients,
        ["Commentaires", "Commentaire"],
        "Commentaires", fill=""
    )

    # 3) Sélection dossier
    dossier_list = df_clients[COL_DOSSIER].astype(str).tolist()
    selected = st.selectbox("Sélectionne un dossier :", [""] + dossier_list, key="gestion_dossier_select")
    if not selected:
        st.stop()

    row = df_clients[df_clients[COL_DOSSIER].astype(str) == str(selected)].iloc[0].copy()

    st.markdown("### 🔧 Modifier le dossier sélectionné")

    # 4) Préremplir champs avec conversions sûres
    nom_val = str(row.get(COL_NOM, ""))
    hono_val = to_float(row.get(COL_HONO, 0))
    ac1_val = to_float(row.get(COL_AC1, 0))
    date_ac1_val = safe_date(row.get(COL_DATE_AC1, ""))
    escrow_flag = str(row.get(COL_ESCROW, "")).strip().lower() in {"oui", "true", "1", "x"}
    comment_val = str(row.get(COL_COMMENT, ""))

    # 5) Formulaire
    c1, c2 = st.columns([2,1])
    with c1:
        nom_val = st.text_input("Nom du client", value=nom_val, key="gestion_nom")
        comment_val = st.text_area("Commentaires", value=comment_val, key="gestion_comment")
    with c2:
        hono_val = st.number_input("Montant honoraires (US $)", min_value=0.0, value=hono_val, step=50.0, key="gestion_hono")
        ac1_val = st.number_input("Acompte 1", min_value=0.0, value=ac1_val, step=50.0, key="gestion_ac1")
        date_ac1_val = st.date_input("Date Acompte 1", value=date_ac1_val, key="gestion_date_ac1")
        escrow_flag = st.checkbox("Escrow ?", value=escrow_flag, key="gestion_escrow_chk")

    st.markdown("---")
    a, b, c = st.columns(3)

    # 6) Enregistrer
    with a:
        if st.button("💾 Enregistrer les modifications", key="gestion_save_btn"):
            idx = df_clients.index[df_clients[COL_DOSSIER].astype(str) == str(selected)][0]
            df_clients.at[idx, COL_NOM] = nom_val
            df_clients.at[idx, COL_HONO] = hono_val
            df_clients.at[idx, COL_AC1] = ac1_val
            df_clients.at[idx, COL_DATE_AC1] = date_ac1_val
            df_clients.at[idx, COL_ESCROW] = "Oui" if escrow_flag else "Non"
            df_clients.at[idx, COL_COMMENT] = comment_val

            # ---------- LOGIQUE ESCROW (dossier courant) ----------
            already = str(selected) in df_escrow["Dossier N"].astype(str).values
            honoraires_zero = (to_float(hono_val) == 0.0)
            acompte_ok = (to_float(ac1_val) > 0.0)

            if (escrow_flag or (acompte_ok and honoraires_zero)) and not already:
                new_row = {
                    "Dossier N": str(selected),
                    "Nom": nom_val,
                    "Montant": to_float(ac1_val),
                    "Date envoi": safe_date(date_ac1_val),
                    "État": "En attente",
                    "Date réclamation": "",
                    "Commentaires": comment_val,
                }
                df_escrow = pd.concat([df_escrow, pd.DataFrame([new_row])], ignore_index=True)
                st.success(f"✅ Dossier {selected} ajouté dans Escrow (courant).")
            elif already:
                st.info(f"ℹ️ Dossier {selected} déjà présent dans Escrow.")
            else:
                st.info("Aucun ajout Escrow requis pour le dossier courant.")

            # ---------- LOGIQUE ESCROW (SCAN GLOBAL) ----------
            # construit une vue normalisée
            tmp = df_clients[[COL_DOSSIER, COL_NOM, COL_HONO, COL_AC1, COL_DATE_AC1, COL_COMMENT]].copy()
            tmp["_hono"] = tmp[COL_HONO].apply(to_float)
            tmp["_ac1"]  = tmp[COL_AC1].apply(to_float)
            tmp["_date"] = tmp[COL_DATE_AC1].apply(safe_date)

            mask = (tmp["_ac1"] > 0.0) & (tmp["_hono"] == 0.0)
            candidats = tmp[mask].copy()

            # Affiche un tableau debug des candidats détectés
            with st.expander("🔎 Debug • Dossiers détectés ‘Acompte > 0 et Honoraires = 0’"):
                if candidats.empty:
                    st.write("Aucun candidat détecté.")
                else:
                    st.write(candidats[[COL_DOSSIER, COL_NOM, COL_AC1, COL_HONO, COL_DATE_AC1]].rename(columns={
                        COL_DOSSIER:"Dossier N", COL_NOM:"Nom", COL_AC1:"Acompte 1", COL_HONO:"Honoraires", COL_DATE_AC1:"Date Acompte 1"
                    }))

            added_ids = []
            for _, r in candidats.iterrows():
                dnum = str(r[COL_DOSSIER])
                if dnum not in df_escrow["Dossier N"].astype(str).values:
                    df_escrow = pd.concat([df_escrow, pd.DataFrame([{
                        "Dossier N": dnum,
                        "Nom": r[COL_NOM],
                        "Montant": to_float(r[COL_AC1]),
                        "Date envoi": safe_date(r[COL_DATE_AC1]),
                        "État": "En attente",
                        "Date réclamation": "",
                        "Commentaires": r.get(COL_COMMENT, ""),
                    }])], ignore_index=True)
                    added_ids.append(dnum)

            if added_ids:
                st.success(f"✅ {len(added_ids)} dossier(s) ajouté(s) à Escrow (scan global) : {', '.join(added_ids)}")

            # push en session
            st.session_state["data_xlsx"]["Clients"] = df_clients
            st.session_state["data_xlsx"]["Escrow"] = df_escrow
            st.success("💾 Modifications enregistrées (mémoire).")

            # Choix sauvegarde
            save_mode = st.radio("Sauvegarder :", ["💻 Local", "☁️ Dropbox"], horizontal=True, key="gestion_save_choice")
            if save_mode == "💻 Local":
                with io.BytesIO() as buffer:
                    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                        for sheet, dfx in st.session_state["data_xlsx"].items():
                            dfx.to_excel(writer, index=False, sheet_name=sheet)
                    buffer.seek(0)
                    st.download_button("⬇️ Télécharger Clients BL.xlsx", buffer, "Clients BL.xlsx",
                                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                       key="gestion_dl_btn")
            else:
                try:
                    token = st.secrets["DROPBOX_TOKEN"]
                    folder = st.secrets.get("DROPBOX_FOLDER", "/")
                    dbx = dropbox.Dropbox(token)
                    with io.BytesIO() as buffer:
                        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                            for sheet, dfx in st.session_state["data_xlsx"].items():
                                dfx.to_excel(writer, index=False, sheet_name=sheet)
                        buffer.seek(0)
                        dbx.files_upload(buffer.read(), f"{folder}/Clients BL.xlsx",
                                         mode=dropbox.files.WriteMode("overwrite"))
                    st.success("☁️ Sauvegardé sur Dropbox.")
                except Exception as e:
                    st.warning(f"⚠️ Sauvegarde Dropbox échouée : {e}")

    with b:
        if st.button("🗑️ Supprimer le dossier", key="gestion_del_btn"):
            df_clients = df_clients[df_clients[COL_DOSSIER].astype(str) != str(selected)]
            st.session_state["data_xlsx"]["Clients"] = df_clients
            st.success(f"🗑️ Dossier {selected} supprimé.")
            st.experimental_rerun()

    with c:
        st.info("💡 Les sauvegardes peuvent être faites localement (download) ou sur Dropbox (secrets).")
