import streamlit as st
import pandas as pd
from datetime import date
from common_data import ensure_loaded, save_all

FILENAME = "Clients BL.xlsx"

def _to_date(val, default=date.today()):
    try:
        if pd.isna(val) or val is None or str(val).strip()=="":
            return default
        return pd.to_datetime(val).date()
    except Exception:
        return default

def tab_gestion():
    st.title("📁 Gestion des dossiers")

    data = ensure_loaded(FILENAME)
    df_clients = data.get("Clients", pd.DataFrame())
    df_visa = data.get("Visa", pd.DataFrame())
    df_escrow = data.get("Escrow", pd.DataFrame())

    st.subheader("🔍 Sélection d’un dossier")
    c1,c2 = st.columns(2)
    dossier_n_sel = c1.selectbox("Par Dossier N°", [""] + sorted(df_clients["Dossier N"].astype(str).unique().tolist()))
    nom_sel = c2.selectbox("Ou par Nom", [""] + sorted(df_clients["Nom"].astype(str).unique().tolist()))

    dossier_data = pd.Series(dtype=object)
    if dossier_n_sel:
        dossier_data = df_clients[df_clients["Dossier N"].astype(str)==str(dossier_n_sel)].iloc[0]
    elif nom_sel:
        dossier_data = df_clients[df_clients["Nom"].astype(str)==str(nom_sel)].iloc[0]
    else:
        st.info("👈 Sélectionne un dossier.")
        return

    st.divider()
    st.subheader("🗂️ Informations générales")
    g1,g2,g3 = st.columns(3)
    dossier_n = g1.text_input("Dossier N°", dossier_data.get("Dossier N",""))
    nom = g2.text_input("Nom du client", dossier_data.get("Nom",""))
    date_creation = g3.date_input("Date (création)", value=_to_date(dossier_data.get("Date")))

    st.subheader("🏷️ Classification et Visa")
    cats = df_visa["Catégories"].dropna().unique().tolist() if "Catégories" in df_visa else []
    sous_cats = df_visa["Sous-catégories"].dropna().unique().tolist() if "Sous-catégories" in df_visa else []
    visas = df_visa["Visa"].dropna().unique().tolist() if "Visa" in df_visa else []
    c3,c4,c5 = st.columns(3)
    cat_sel = c3.selectbox("Catégorie", [""]+cats, index=([""]+cats).index(dossier_data.get("Catégories","")) if dossier_data.get("Catégories","") in cats else 0)
    sous_cat_sel = c4.selectbox("Sous-catégorie", [""]+sous_cats, index=([""]+sous_cats).index(dossier_data.get("Sous-catégories","")) if dossier_data.get("Sous-catégories","") in sous_cats else 0)
    visa_sel = c5.selectbox("Visa", [""]+visas, index=([""]+visas).index(dossier_data.get("Visa","")) if dossier_data.get("Visa","") in visas else 0)

    st.subheader("💵 Paiements")
    p1,p2,p3 = st.columns(3)
    montant_hono = p1.number_input("Montant honoraires (US $)", value=float(dossier_data.get("Montant honoraires (US $)",0)))
    acompte1_date = p2.date_input("Date Acompte 1", value=_to_date(dossier_data.get("Date Acompte 1")))
    acompte1 = p3.number_input("Acompte 1 (US $)", value=float(dossier_data.get("Acompte 1",0)))

    m1,m2,m3,m4 = st.columns(4)
    mode = dossier_data.get("Mode de paiement","")
    mode_cheque = m1.checkbox("Chèque", value=(mode=="Chèque"))
    mode_virement = m2.checkbox("Virement", value=(mode=="Virement"))
    mode_cb = m3.checkbox("Carte bancaire", value=(mode=="Carte bancaire"))
    mode_venmo = m4.checkbox("Venmo", value=(mode=="Venmo"))
    mode_paiement = "Chèque" if mode_cheque else "Virement" if mode_virement else "Carte bancaire" if mode_cb else "Venmo" if mode_venmo else ""

    escrow_checked = st.checkbox("Escrow", value=bool(dossier_data.get("Escrow", False)))

    st.subheader("📌 Statut du dossier")
    s1,s2 = st.columns([1,1])
    dossier_envoye = s1.checkbox("Dossier envoyé", value=bool(dossier_data.get("Dossier envoyé", False)))
    date_envoye = s2.date_input("Date envoi", value=_to_date(dossier_data.get("Date envoi")))

    s3,s4 = st.columns(2)
    dossier_accepte = s3.checkbox("Dossier accepté", value=bool(dossier_data.get("Dossier accepté", False)))
    date_accepte = s4.date_input("Date acceptation", value=_to_date(dossier_data.get("Date acceptation")))

    s5,s6 = st.columns(2)
    dossier_refuse = s5.checkbox("Dossier refusé", value=bool(dossier_data.get("Dossier refusé", False)))
    date_refuse = s6.date_input("Date refus", value=_to_date(dossier_data.get("Date refus")))

    s7,s8 = st.columns(2)
    dossier_annule = s7.checkbox("Dossier annulé", value=bool(dossier_data.get("Dossier annulé", False)))
    date_annule = s8.date_input("Date annulation", value=_to_date(dossier_data.get("Date annulation")))

    rfe = st.checkbox("RFE obligatoire", value=bool(dossier_data.get("RFE", False)))

    commentaires = st.text_area("Commentaires", value=dossier_data.get("Commentaires",""), height=100)

    if st.button("💾 Enregistrer les modifications"):
        try:
            idx = df_clients[df_clients["Dossier N"].astype(str)==str(dossier_data["Dossier N"])].index[0]
            df_clients.loc[idx, "Dossier N"] = dossier_n
            df_clients.loc[idx, "Nom"] = nom
            df_clients.loc[idx, "Date"] = date_creation
            df_clients.loc[idx, "Catégories"] = cat_sel
            df_clients.loc[idx, "Sous-catégories"] = sous_cat_sel
            df_clients.loc[idx, "Visa"] = visa_sel
            df_clients.loc[idx, "Montant honoraires (US $)"] = montant_hono
            df_clients.loc[idx, "Acompte 1"] = acompte1
            df_clients.loc[idx, "Date Acompte 1"] = acompte1_date
            df_clients.loc[idx, "Mode de paiement"] = mode_paiement
            df_clients.loc[idx, "Escrow"] = escrow_checked

            df_clients.loc[idx, "Dossier envoyé"] = dossier_envoye
            df_clients.loc[idx, "Date envoi"] = date_envoye
            df_clients.loc[idx, "Dossier accepté"] = dossier_accepte
            df_clients.loc[idx, "Date acceptation"] = date_accepte
            df_clients.loc[idx, "Dossier refusé"] = dossier_refuse
            df_clients.loc[idx, "Date refus"] = date_refuse
            df_clients.loc[idx, "Dossier annulé"] = dossier_annule
            df_clients.loc[idx, "Date annulation"] = date_annule
            df_clients.loc[idx, "RFE"] = rfe
            df_clients.loc[idx, "Commentaires"] = commentaires

            # Escrow auto si acompte>0 et honoraire==0
            will_escrow = escrow_checked or (acompte1 > 0 and float(montant_hono)==0.0)
            if will_escrow:
                df_escrow = data.get("Escrow", pd.DataFrame(columns=["Dossier N","Nom","Montant","Date envoi","Etat","Date réclamation"]))
                if str(dossier_n) not in df_escrow["Dossier N"].astype(str).values:
                    new_line = pd.DataFrame({
                        "Dossier N":[dossier_n],
                        "Nom":[nom],
                        "Montant":[acompte1],
                        "Date envoi":[date_envoye],
                        "Etat":["En attente"],
                        "Date réclamation":[""]
                    })
                    df_escrow = pd.concat([df_escrow, new_line], ignore_index=True)
                    data["Escrow"] = df_escrow

            data["Clients"] = df_clients
            st.session_state["data_xlsx"] = data
            save_all(FILENAME)

            # reset sélection pour pouvoir en choisir un autre de suite
            st.session_state["gestion_dossier_num"] = ""
            st.session_state["gestion_nom"] = ""
            st.success("✅ Modifications enregistrées.")
            st.rerun()
        except Exception as e:
            st.error(f"❌ Erreur : {e}")
