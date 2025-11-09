import streamlit as st
import pandas as pd
from datetime import date
import dropbox
import io
import os

DROPBOX_TOKEN = os.getenv("DROPBOX_TOKEN")   # définir dans Streamlit Cloud (Secrets)
DROPBOX_PATH  = "/Clients-BL.xlsx"

ESCROW_COLUMNS = ["Dossier N", "Nom", "Montant", "Date envoi", "État", "Date réclamation"]

def _safe_to_date(v, default=date.today()):
    """Convertit valeur Excel/str -> date (objet) sans planter."""
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
    """Retourne la clé réelle de la feuille Escrow (insensible à la casse), en la créant si besoin."""
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
        # Garantir les colonnes
        for c in ESCROW_COLUMNS:
            if c not in data_dict[escrow_key].columns:
                data_dict[escrow_key][c] = ""
        data_dict[escrow_key] = data_dict[escrow_key][ESCROW_COLUMNS]
    return escrow_key

def _upsert_escrow_row(data_dict, escrow_key, dossier_n, nom, montant, etat, date_envoi=""):
    """Crée ou met à jour une ligne Escrow pour un dossier."""
    df_e = data_dict[escrow_key].copy()
    dossier_n_str = str(dossier_n)
    mask = df_e["Dossier N"].astype(str) == dossier_n_str
    if mask.any():
        i = df_e.index[mask][0]
        if nom not in ("", None):
            df_e.at[i, "Nom"] = nom
        if montant is not None:
            df_e.at[i, "Montant"] = float(montant)
        if date_envoi is not None:
            df_e.at[i, "Date envoi"] = date_envoi
        if etat:
            df_e.at[i, "État"] = etat
        data_dict[escrow_key] = df_e
        return
    # sinon, insertion
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

def tab_gestion():
    """Onglet de gestion et mise à jour des dossiers existants (avec Escrow automatique)."""
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

    # ================= Sélection du dossier =================
    st.subheader("🔎 Sélection du dossier")
    col_sel1, col_sel2 = st.columns(2)
    dossier_list = sorted(df["Dossier N"].dropna().astype(str).tolist()) if "Dossier N" in df else []
    nom_list     = sorted(df["Nom"].dropna().astype(str).tolist()) if "Nom" in df else []

    sel_dossier = col_sel1.selectbox("Dossier N", options=[""] + dossier_list, key="gestion_sel_dossier")
    sel_nom     = col_sel2.selectbox("Nom du client", options=[""] + nom_list, key="gestion_sel_nom")

    # Synchronisation
    dossier_data = None
    if sel_dossier:
        m = df["Dossier N"].astype(str) == sel_dossier
        if m.any():
            dossier_data = df[m].iloc[0].to_dict()
    elif sel_nom:
        m = df["Nom"].astype(str) == sel_nom
        if m.any():
            dossier_data = df[m].iloc[0].to_dict()

    if dossier_data is None:
        st.info("Sélectionnez un dossier pour le modifier.")
        return

    # ================= Informations principales =================
    st.subheader("🧾 Informations principales")
    c1, c2, c3 = st.columns(3)
    dossier_n = c1.text_input("Dossier N", value=str(dossier_data.get("Dossier N", "")), key="gestion_dossier_n")
    nom_client = c2.text_input("Nom du client", value=str(dossier_data.get("Nom", "")), key="gestion_nom")
    date_creation = c3.date_input(
        "Date (création)",
        value=_safe_to_date(dossier_data.get("Date création", dossier_data.get("Date", date.today()))),
        key="gestion_date_creation"
    )

    # ================= Classification et Visa =================
    st.subheader("📂 Classification et visa")
    col1, col2, col3 = st.columns(3)

    df_visa = data.get("Visa", pd.DataFrame())
    categories = sorted(df_visa["Catégorie"].dropna().unique().tolist()) if "Catégorie" in df_visa else []
    selected_cat_current = str(dossier_data.get("Catégories", ""))
    selected_cat = col1.selectbox(
        "Catégorie",
        options=[""] + categories,
        index=([""] + categories).index(selected_cat_current) if selected_cat_current in categories else 0,
        key="gestion_categorie"
    )

    souscats = []
    if selected_cat and "Sous-catégorie" in df_visa:
        souscats = sorted(df_visa[df_visa["Catégorie"] == selected_cat]["Sous-catégorie"].dropna().unique().tolist())
    selected_souscat_current = str(dossier_data.get("Sous-catégories", ""))
    selected_souscat = col2.selectbox(
        "Sous-catégorie",
        options=[""] + souscats,
        index=([""] + souscats).index(selected_souscat_current) if selected_souscat_current in souscats else 0,
        key="gestion_souscategorie"
    )

    visas = sorted(df_visa.columns[3:].tolist()) if not df_visa.empty else []
    selected_visa_current = str(dossier_data.get("Visa", ""))
    selected_visa = col3.selectbox(
        "Visa",
        options=[""] + visas,
        index=([""] + visas).index(selected_visa_current) if selected_visa_current in visas else 0,
        key="gestion_visa"
    )

    # ================= Informations financières =================
    st.subheader("💵 Informations financières")
    c4, c5, c6 = st.columns(3)
    montant_hono = c4.number_input(
        "Montant honoraires (US $)", min_value=0.0, step=100.0, format="%.2f",
        value=float(_to_float(dossier_data.get("Montant honoraires (US $)", 0.0))),
        key="gestion_mh"
    )
    date_acompte1 = c5.date_input(
        "Date Acompte 1",
        value=_safe_to_date(dossier_data.get("Date Acompte 1", date.today())),
        key="gestion_date_ac1"
    )
    acompte1 = c6.number_input(
        "Acompte 1 (US $)", min_value=0.0, step=100.0, format="%.2f",
        value=float(_to_float(dossier_data.get("Acompte 1", 0.0))),
        key="gestion_ac1"
    )

    # ================= Acomptes 2→4 =================
    st.subheader("💰 Acomptes supplémentaires")
    ac_inputs = []
    for i in range(2, 5):
        cc1, cc2, cc3 = st.columns(3)
        val_mnt = float(_to_float(dossier_data.get(f"Acompte {i}", 0.0)))
        val_date = _safe_to_date(dossier_data.get(f"Date Acompte {i}", None))
        modes_exist = str(dossier_data.get(f"Mode paiement {i}", "") or "")
        pre_modes = [m.strip() for m in modes_exist.split(",") if m.strip()]

        mnt = cc1.number_input(f"Acompte {i} (US $)", min_value=0.0, step=100.0, format="%.2f", value=val_mnt, key=f"gestion_ac{i}")
        dat = cc2.date_input(f"Date Acompte {i}", value=val_date, key=f"gestion_date_ac{i}")
        modes = cc3.multiselect(f"Mode paiement Acompte {i}", ["Chèque", "Virement", "Carte bancaire", "Venmo"], default=pre_modes, key=f"gestion_mode_ac{i}")
        ac_inputs.append((i, mnt, dat, modes))

    # ================= Mode de paiement Acompte 1 =================
    st.subheader("💳 Mode de paiement Acompte 1")
    col_mp1, col_mp2, col_mp3, col_mp4 = st.columns(4)
    existing_mode1 = str(dossier_data.get("Mode paiement 1", "") or "")
    defaults1 = [m.strip() for m in existing_mode1.split(",") if m.strip()]
    mode1 = col_mp1.checkbox("Chèque",  value=("Chèque" in defaults1), key="gestion_mp1_chq")
    mode2 = col_mp2.checkbox("Virement", value=("Virement" in defaults1), key="gestion_mp1_vir")
    mode3 = col_mp3.checkbox("Carte bancaire", value=("Carte bancaire" in defaults1), key="gestion_mp1_cb")
    mode4 = col_mp4.checkbox("Venmo", value=("Venmo" in defaults1), key="gestion_mp1_ven")
    mode_paiement_1 = ", ".join([label for label, flag in [
        ("Chèque", mode1), ("Virement", mode2), ("Carte bancaire", mode3), ("Venmo", mode4)
    ] if flag])

    # ================= Escrow & Envoi =================
    st.subheader("🛡️ Escrow")
    escrow_initial = str(dossier_data.get("Escrow", "")).strip().lower() == "oui"
    escrow_box = st.checkbox("Envoyé en Escrow", value=escrow_initial, key="gestion_escrow")

    st.subheader("📤 Envoi du dossier")
    col_e1, col_e2 = st.columns(2)
    envoye = col_e1.checkbox("Dossier envoyé", value=(str(dossier_data.get("Dossier envoyé", "")).lower() == "oui"), key="gestion_envoye")
    date_envoi = col_e2.date_input(
        "Date envoi",
        value=_safe_to_date(dossier_data.get("Date envoi", date.today())),
        key="gestion_date_envoi"
    )

    # Si "Dossier envoyé" est coché -> le dossier devient "À réclamer" en Escrow
    # (déblocage)
    if envoye:
        escrow_box = True  # s'assurer qu'il est bien suivi en Escrow pour réclamation

    st.subheader("📝 Commentaires")
    commentaires = st.text_area("Commentaires", value=str(dossier_data.get("Commentaires", "") or ""), key="gestion_comment")

    st.markdown("---")

    # ================= Sauvegarde =================
    if st.button("💾 Enregistrer les modifications", key="gestion_save"):
        # Localiser la ligne
        idx = df.index[df["Dossier N"].astype(str) == str(dossier_n)]
        if idx.empty:
            st.error("❌ Dossier introuvable.")
            return
        i = idx[0]

        # Écrire les champs Clients
        df.loc[i, "Nom"] = nom_client
        df.loc[i, "Date création"] = date_creation.strftime("%Y-%m-%d")
        df.loc[i, "Catégories"] = selected_cat
        df.loc[i, "Sous-catégories"] = selected_souscat
        df.loc[i, "Visa"] = selected_visa

        df.loc[i, "Montant honoraires (US $)"] = float(montant_hono or 0.0)
        df.loc[i, "Acompte 1"] = float(acompte1 or 0.0)
        df.loc[i, "Date Acompte 1"] = date_acompte1.strftime("%Y-%m-%d")
        df.loc[i, "Mode paiement 1"] = mode_paiement_1

        for j, mnt, dat, modes in ac_inputs:
            df.loc[i, f"Acompte {j}"] = float(mnt or 0.0)
            df.loc[i, f"Date Acompte {j}"] = dat.strftime("%Y-%m-%d") if isinstance(dat, date) else _safe_to_date(dat).strftime("%Y-%m-%d")
            df.loc[i, f"Mode paiement {j}"] = ", ".join(modes)

        # Escrow / Envoi
        df.loc[i, "Dossier envoyé"] = "Oui" if envoye else "Non"
        df.loc[i, "Date envoi"] = date_envoi.strftime("%Y-%m-%d") if isinstance(date_envoi, date) else _safe_to_date(date_envoi).strftime("%Y-%m-%d")

        # ====== RÈGLE ESCROW AUTOMATIQUE ======
        # Si Acompte 1 > 0 et Montant honoraires = 0 -> doit être en Escrow
        auto_escrow = (float(acompte1 or 0.0) > 0.0) and (float(montant_hono or 0.0) == 0.0)
        escrow_final = escrow_box or auto_escrow

        df.loc[i, "Escrow"] = "Oui" if escrow_final else "Non"

        # ====== Synchronisation feuille Escrow ======
        escrow_key = _ensure_escrow_sheet(data)

        if escrow_final:
            # Si envoyé -> marquer "À réclamer" avec Date envoi ; sinon "En attente"
            etat = "À réclamer" if envoye else "En attente"
            date_env_str = df.loc[i, "Date envoi"] if envoye else ""
            _upsert_escrow_row(
                data, escrow_key,
                dossier_n=dossier_n,
                nom=nom_client,
                montant=float(acompte1 or 0.0),
                etat=etat,
                date_envoi=date_env_str
            )
        else:
            # Non escrow -> retirer si existait (et non envoyé)
            if not envoye:
                _remove_escrow_row(data, escrow_key, dossier_n)

        # Écriture mémoire
        st.session_state["data_xlsx"]["Clients"] = df

        # Sauvegarde Dropbox (si token)
        try:
            if DROPBOX_TOKEN:
                dbx = dropbox.Dropbox(DROPBOX_TOKEN)
                with io.BytesIO() as buffer:
                    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                        # Clients mis à jour
                        st.session_state["data_xlsx"]["Clients"].to_excel(writer, sheet_name="Clients", index=False)
                        # Autres feuilles
                        for sheet_name, sheet_df in st.session_state["data_xlsx"].items():
                            if sheet_name == "Clients":
                                continue
                            # garantir dataframe
                            if isinstance(sheet_df, dict):
                                sheet_df = pd.DataFrame(sheet_df)
                            sheet_df.to_excel(writer, sheet_name=sheet_name, index=False)
                    buffer.seek(0)
                    dbx.files_upload(buffer.read(), DROPBOX_PATH, mode=dropbox.files.WriteMode.overwrite)
                st.success("✅ Modifications sauvegardées sur Dropbox.")
            else:
                st.warning("⚠️ Aucun token Dropbox — modifications gardées en mémoire uniquement.")
        except Exception as e:
            st.error(f"❌ Erreur Dropbox : {e}")

        st.success("✅ Dossier mis à jour. Escrow synchronisé.")
        st.rerun()
