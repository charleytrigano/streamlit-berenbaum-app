import streamlit as st
import pandas as pd
from datetime import date
import dropbox
import io
import os

DROPBOX_TOKEN = os.getenv("DROPBOX_TOKEN")
DROPBOX_PATH = "/Clients-BL.xlsx"
ESCROW_COLUMNS = ["Dossier N", "Nom", "Montant", "Date envoi", "État", "Date réclamation"]

# --------------------------------------------------------------------
# Fonctions utilitaires
# --------------------------------------------------------------------
def _safe_to_date(v, default=date.today()):
    try:
        if pd.isna(v) or v in ("", None):
            return default
        ts = pd.to_datetime(v, errors="coerce")
        if pd.isna(ts):
            return default
        return ts.date()
    except Exception:
        return default

def _to_float(x):
    try:
        s = str(x).replace("\u00A0", "").replace(",", ".").strip()
        return float(s) if s not in ("", "nan", "None") else 0.0
    except Exception:
        return 0.0

def _ensure_escrow_sheet(data_dict):
    escrow_key = None
    for k in data_dict.keys():
        if "escrow" in k.strip().lower():
            escrow_key = k
            break
    if escrow_key is None:
        escrow_key = "Escrow"
        data_dict[escrow_key] = pd.DataFrame(columns=ESCROW_COLUMNS)
    else:
        df_e = data_dict[escrow_key]
        if isinstance(df_e, dict):
            data_dict[escrow_key] = pd.DataFrame(df_e)
        for c in ESCROW_COLUMNS:
            if c not in data_dict[escrow_key].columns:
                data_dict[escrow_key][c] = ""
        data_dict[escrow_key] = data_dict[escrow_key][ESCROW_COLUMNS]
    return escrow_key

def _upsert_escrow_row(data_dict, escrow_key, dossier_n, nom, montant, etat, date_envoi=""):
    df_e = data_dict[escrow_key].copy()
    dossier_n_str = str(dossier_n)
    mask = df_e["Dossier N"].astype(str) == dossier_n_str
    if mask.any():
        i = df_e.index[mask][0]
        df_e.at[i, "Nom"] = nom or ""
        df_e.at[i, "Montant"] = float(montant or 0)
        df_e.at[i, "Date envoi"] = date_envoi or ""
        df_e.at[i, "État"] = etat or "En attente"
        data_dict[escrow_key] = df_e
        return
    new_row = {
        "Dossier N": dossier_n_str,
        "Nom": nom or "",
        "Montant": float(montant or 0.0),
        "Date envoi": date_envoi or "",
        "État": etat or "En attente",
        "Date réclamation": ""
    }
    data_dict[escrow_key] = pd.concat([df_e, pd.DataFrame([new_row])], ignore_index=True)

def _remove_escrow_row(data_dict, escrow_key, dossier_n):
    df_e = data_dict[escrow_key].copy()
    dossier_n_str = str(dossier_n)
    data_dict[escrow_key] = df_e[df_e["Dossier N"].astype(str) != dossier_n_str].reset_index(drop=True)

# --------------------------------------------------------------------
# Onglet principal
# --------------------------------------------------------------------
def tab_gestion():
    st.header("🗂️ Gestion des dossiers")

    if "data_xlsx" not in st.session_state or not st.session_state["data_xlsx"]:
        st.warning("⚠️ Chargez d'abord le fichier Excel via l’onglet 📄 Fichiers.")
        return
    data = st.session_state["data_xlsx"]
    if "Clients" not in data:
        st.error("❌ Feuille 'Clients' absente du fichier Excel.")
        return
    df = data["Clients"].copy()
    if df.empty:
        st.warning("📄 Aucun dossier client.")
        return

    # ---------------- Vérification automatique des dossiers Escrow ----------------
    st.markdown("### 🔍 Vérification automatique des dossiers à placer en Escrow")
    escrow_key = _ensure_escrow_sheet(data)
    auto_escrow_count = 0

    for _, row in df.iterrows():
        acompte = _to_float(row.get("Acompte 1", 0))
        honor = _to_float(row.get("Montant honoraires (US $)", 0))
        if acompte > 0 and honor == 0:
            dossier_n = row.get("Dossier N", "")
            nom = row.get("Nom", "")
            if dossier_n and nom:
                _upsert_escrow_row(data, escrow_key, dossier_n, nom, acompte, "En attente")
                auto_escrow_count += 1

    if auto_escrow_count > 0:
        st.info(f"✅ {auto_escrow_count} dossiers ont été automatiquement ajoutés à Escrow.")
        st.session_state["data_xlsx"]["Escrow"] = data[escrow_key]

    # ---------------- Sélection dossier ----------------
    st.subheader("🔎 Sélection du dossier")
    c1, c2 = st.columns(2)
    dossiers = sorted(df["Dossier N"].dropna().astype(str).tolist())
    noms = sorted(df["Nom"].dropna().astype(str).tolist())
    sel_dossier = c1.selectbox("Dossier N", [""] + dossiers, key="gestion_sel_dossier")
    sel_nom = c2.selectbox("Nom du client", [""] + noms, key="gestion_sel_nom")

    dossier_data = None
    if sel_dossier:
        dossier_data = df[df["Dossier N"].astype(str) == sel_dossier].iloc[0].to_dict()
    elif sel_nom:
        dossier_data = df[df["Nom"].astype(str) == sel_nom].iloc[0].to_dict()
    if dossier_data is None:
        st.info("Sélectionnez un dossier à modifier.")
        return

    # ---------------- Informations principales ----------------
    st.subheader("🧾 Informations principales")
    c1, c2, c3 = st.columns(3)
    dossier_n = c1.text_input("Dossier N", dossier_data.get("Dossier N", ""), key="gestion_dossier")
    nom_client = c2.text_input("Nom du client", dossier_data.get("Nom", ""), key="gestion_nom")
    date_creation = c3.date_input(
        "Date (création)",
        value=_safe_to_date(dossier_data.get("Date création", date.today())),
        key="gestion_date_creation"
    )

    # ---------------- Catégories et visa ----------------
    st.subheader("📂 Classification et visa")
    c1, c2, c3 = st.columns(3)

    df_visa = data.get("Visa", pd.DataFrame())
    if not df_visa.empty:
        df_visa.columns = df_visa.columns.map(str)
        df_visa = df_visa.dropna(how="all")

    cats = sorted(df_visa["Catégorie"].dropna().unique().tolist()) if "Catégorie" in df_visa else []
    cat_sel = c1.selectbox(
        "Catégorie",
        [""] + cats,
        index=([""] + cats).index(dossier_data.get("Catégories", "")) if dossier_data.get("Catégories", "") in cats else 0,
        key="gestion_cat"
    )

    souscats = []
    if cat_sel and "Sous-catégorie" in df_visa:
        souscats = df_visa.loc[df_visa["Catégorie"] == cat_sel, "Sous-catégorie"].dropna().unique().tolist()
    sous_sel = c2.selectbox(
        "Sous-catégorie",
        [""] + sorted(souscats),
        index=([""] + sorted(souscats)).index(dossier_data.get("Sous-catégories", "")) if dossier_data.get("Sous-catégories", "") in souscats else 0,
        key="gestion_souscat"
    )

    visas = sorted(df_visa.columns[3:].tolist()) if not df_visa.empty else []
    visa_sel = c3.selectbox(
        "Visa",
        [""] + visas,
        index=([""] + visas).index(dossier_data.get("Visa", "")) if dossier_data.get("Visa", "") in visas else 0,
        key="gestion_visa"
    )

    # ---------------- Montants et acomptes ----------------
    st.subheader("💵 Informations financières")
    c1, c2, c3 = st.columns(3)
    honoraires = c1.number_input("Montant honoraires (US $)", min_value=0.0, step=100.0, format="%.2f",
                                 value=float(_to_float(dossier_data.get("Montant honoraires (US $)", 0.0))), key="gestion_honoraires")
    date_a1 = c2.date_input("Date Acompte 1", value=_safe_to_date(dossier_data.get("Date Acompte 1", date.today())), key="gestion_date_a1")
    acompte1 = c3.number_input("Acompte 1 (US $)", min_value=0.0, step=100.0, format="%.2f",
                               value=float(_to_float(dossier_data.get("Acompte 1", 0.0))), key="gestion_acompte1")

    st.subheader("💳 Mode de paiement Acompte 1")
    m1, m2, m3, m4 = st.columns(4)
    existing = str(dossier_data.get("Mode paiement 1", "") or "")
    defaults = [m.strip() for m in existing.split(",") if m.strip()]
    mode1 = m1.checkbox("Chèque", value=("Chèque" in defaults), key="gestion_mode1")
    mode2 = m2.checkbox("Virement", value=("Virement" in defaults), key="gestion_mode2")
    mode3 = m3.checkbox("Carte bancaire", value=("Carte bancaire" in defaults), key="gestion_mode3")
    mode4 = m4.checkbox("Venmo", value=("Venmo" in defaults), key="gestion_mode4")
    mode_paiement_1 = ", ".join([label for label, flag in [
        ("Chèque", mode1), ("Virement", mode2), ("Carte bancaire", mode3), ("Venmo", mode4)
    ] if flag])

    # ---------------- Statut du dossier ----------------
    st.subheader("📌 Statut du dossier")
    c1, c2 = st.columns(2)
    accepte = c1.checkbox("✅ Dossier accepté", value=(str(dossier_data.get("Dossier accepté", "")).lower() == "oui"), key="gestion_accepte")
    date_acc = c2.date_input("Date acceptation", value=_safe_to_date(dossier_data.get("Date acceptation", date.today())), key="gestion_date_acc")

    c3, c4 = st.columns(2)
    refuse = c3.checkbox("❌ Dossier refusé", value=(str(dossier_data.get("Dossier refusé", "")).lower() == "oui"), key="gestion_refuse")
    date_ref = c4.date_input("Date refus", value=_safe_to_date(dossier_data.get("Date refus", date.today())), key="gestion_date_ref")

    c5, c6 = st.columns(2)
    annule = c5.checkbox("🚫 Dossier annulé", value=(str(dossier_data.get("Dossier annulé", "")).lower() == "oui"), key="gestion_annule")
    date_ann = c6.date_input("Date annulation", value=_safe_to_date(dossier_data.get("Date annulation", date.today())), key="gestion_date_ann")

    rfe = st.checkbox("⚠️ RFE (Request For Evidence)", value=(str(dossier_data.get("RFE", "")).lower() == "oui"), key="gestion_rfe")

    # Validation logique RFE
    if (accepte or refuse or annule) and not rfe:
        st.error("⚠️ Vous devez cocher la case 'RFE' si le dossier est accepté, refusé ou annulé.")
        return

    # ---------------- Escrow & envoi ----------------
    st.subheader("🛡️ Escrow")
    escrow_box = st.checkbox("Envoyé en Escrow", value=(str(dossier_data.get("Escrow", "")).lower() == "oui"), key="gestion_escrow")
    st.subheader("📤 Envoi du dossier")
    c1, c2 = st.columns(2)
    envoye = c1.checkbox("Dossier envoyé", value=(str(dossier_data.get("Dossier envoyé", "")).lower() == "oui"), key="gestion_envoye")
    date_env = c2.date_input("Date envoi", value=_safe_to_date(dossier_data.get("Date envoi", date.today())), key="gestion_date_env")

    st.subheader("📝 Commentaires")
    comment = st.text_area("Commentaires", value=dossier_data.get("Commentaires", ""), key="gestion_comment")
    st.markdown("---")

    # ---------------- Sauvegarde ----------------
    if st.button("💾 Enregistrer les modifications", key="gestion_save_btn"):
        idx = df.index[df["Dossier N"].astype(str) == str(dossier_n)]
        if idx.empty:
            st.error("❌ Dossier introuvable.")
            return
        i = idx[0]

        # Met à jour le dossier
        df.loc[i, "Nom"] = nom_client
        df.loc[i, "Date création"] = date_creation.strftime("%Y-%m-%d")
        df.loc[i, "Catégories"] = cat_sel
        df.loc[i, "Sous-catégories"] = sous_sel
        df.loc[i, "Visa"] = visa_sel
        df.loc[i, "Montant honoraires (US $)"] = honoraires
        df.loc[i, "Acompte 1"] = acompte1
        df.loc[i, "Date Acompte 1"] = date_a1.strftime("%Y-%m-%d")
        df.loc[i, "Mode paiement 1"] = mode_paiement_1
        df.loc[i, "Dossier accepté"] = "Oui" if accepte else "Non"
        df.loc[i, "Date acceptation"] = date_acc.strftime("%Y-%m-%d")
        df.loc[i, "Dossier refusé"] = "Oui" if refuse else "Non"
        df.loc[i, "Date refus"] = date_ref.strftime("%Y-%m-%d")
        df.loc[i, "Dossier annulé"] = "Oui" if annule else "Non"
        df.loc[i, "Date annulation"] = date_ann.strftime("%Y-%m-%d")
        df.loc[i, "RFE"] = "Oui" if rfe else "Non"
        df.loc[i, "Dossier envoyé"] = "Oui" if envoye else "Non"
        df.loc[i, "Date envoi"] = date_env.strftime("%Y-%m-%d")
        df.loc[i, "Commentaires"] = comment

        # Escrow automatique ou manuel
        auto_escrow = acompte1 > 0 and honoraires == 0
        escrow_final = escrow_box or auto_escrow
        df.loc[i, "Escrow"] = "Oui" if escrow_final else "Non"

        escrow_key = _ensure_escrow_sheet(data)
        if escrow_final:
            etat = "À réclamer" if envoye else "En attente"
            date_env_str = df.loc[i, "Date envoi"] if envoye else ""
            _upsert_escrow_row(data, escrow_key, dossier_n, nom_client, acompte1, etat, date_env_str)
            st.session_state["data_xlsx"][escrow_key] = data[escrow_key]
        else:
            _remove_escrow_row(data, escrow_key, dossier_n)
            st.session_state["data_xlsx"][escrow_key] = data[escrow_key]

        st.session_state["data_xlsx"]["Clients"] = df

        # Sauvegarde Dropbox
        try:
            if DROPBOX_TOKEN:
                dbx = dropbox.Dropbox(DROPBOX_TOKEN)
                with io.BytesIO() as buffer:
                    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                        for sheet, sheet_df in st.session_state["data_xlsx"].items():
                            pd.DataFrame(sheet_df).to_excel(writer, sheet_name=sheet, index=False)
                    buffer.seek(0)
                    dbx.files_upload(buffer.read(), DROPBOX_PATH, mode=dropbox.files.WriteMode.overwrite)
                st.success("✅ Modifications sauvegardées sur Dropbox.")
            else:
                st.warning("⚠️ Aucun token Dropbox — sauvegarde locale uniquement.")
        except Exception as e:
            st.error(f"❌ Erreur Dropbox : {e}")

        st.session_state["data_xlsx"]["Escrow"] = data[escrow_key]
        st.success(f"✅ Dossier mis à jour{' et envoyé en Escrow' if escrow_final else ''}.")
        st.rerun()
