import streamlit as st
import pandas as pd

def tab_dashboard():
    """Tableau de bord principal - synthèse financière + synchronisation Escrow automatique."""
    st.header("📊 Tableau de bord")

    # Vérif fichier
    if "data_xlsx" not in st.session_state or not st.session_state["data_xlsx"]:
        st.warning("⚠️ Aucune donnée disponible. Chargez le fichier Excel via 📄 Fichiers.")
        return

    data = st.session_state["data_xlsx"]

    if "Clients" not in data:
        st.error("❌ Feuille 'Clients' absente du fichier Excel.")
        return

    df = data["Clients"].copy()
    if df.empty:
        st.warning("📄 La feuille 'Clients' est vide.")
        return

    # Conversion propre
    def _to_float(x):
        try:
            s = str(x).replace(",", ".").replace("\u00A0", "").strip()
            return float(s) if s not in ["", "nan", "None"] else 0.0
        except:
            return 0.0

    for col in ["Montant honoraires (US $)", "Autres frais (US $)", "Acompte 1"]:
        if col in df.columns:
            df[col] = df[col].map(_to_float)
        else:
            df[col] = 0.0

    # ==============================
    # 🧠 Détection automatique des Escrow
    # ==============================
    escrow_key = None
    for key in data.keys():
        if key.strip().lower() == "escrow":
            escrow_key = key
            break

    if not escrow_key:
        st.warning("⚠️ Feuille Escrow non trouvée. Création automatique possible au prochain enregistrement.")
        escrow_df = pd.DataFrame(columns=["Dossier N", "Nom", "Montant", "Date envoi", "État", "Date réclamation"])
    else:
        escrow_df = data[escrow_key].copy()

    # Recherche des dossiers à transférer
    if all(col in df.columns for col in ["Acompte 1", "Montant honoraires (US $)", "Nom", "Dossier N"]):
        auto_escrow = df[(df["Acompte 1"] > 0) & (df["Montant honoraires (US $)"] == 0)][["Dossier N", "Nom", "Acompte 1"]].copy()
        auto_escrow.rename(columns={"Acompte 1": "Montant"}, inplace=True)

        # Ajoute les nouveaux dossiers manquants
        existing_ids = set(escrow_df["Dossier N"].astype(str).tolist()) if not escrow_df.empty else set()
        new_rows = auto_escrow[~auto_escrow["Dossier N"].astype(str).isin(existing_ids)]

        if not new_rows.empty:
            new_rows["Date envoi"] = pd.Timestamp.now().strftime("%Y-%m-%d")
            new_rows["État"] = "En attente"
            new_rows["Date réclamation"] = ""
            escrow_df = pd.concat([escrow_df, new_rows], ignore_index=True)

            # Met à jour les données en mémoire
            data[escrow_key] = escrow_df
            st.session_state["data_xlsx"] = data
            st.info(f"✅ {len(new_rows)} dossiers ajoutés automatiquement dans Escrow.")

    # ==============================
    # 💰 Calculs financiers
    # ==============================
    df["Montant facturé"] = df["Montant honoraires (US $)"] + df["Autres frais (US $)"]
    df["Total payé"] = df["Acompte 1"]
    df["Solde restant"] = df["Montant facturé"] - df["Total payé"]

    montant_facture = df["Montant facturé"].sum()
    montant_paye = df["Total payé"].sum()
    solde_restant = df["Solde restant"].sum()
    n_dossiers = len(df)

    # ==============================
    # 🛡️ Escrow (KPI)
    # ==============================
    escrow_count = len(escrow_df)
    escrow_total = escrow_df["Montant"].map(_to_float).sum() if not escrow_df.empty else 0.0

    # ==============================
    # 📊 KPI
    # ==============================
    st.markdown("### 💼 Synthèse financière")
    k1, k2, k3, k4, k5, k6 = st.columns(6)
    k1.metric("Montant facturé", f"${montant_facture:,.0f}")
    k2.metric("Total payé", f"${montant_paye:,.0f}")
    k3.metric("Solde restant", f"${solde_restant:,.0f}")
    k4.metric("Nb dossiers", f"{n_dossiers}")
    k5.metric("Dossiers Escrow", f"{escrow_count}")
    k6.metric("Montant Escrow", f"${escrow_total:,.0f}")

    st.markdown("---")

    # ==============================
    # 📋 Tableau Clients
    # ==============================
    st.subheader("📁 Dossiers clients (aperçu)")
    colonnes = [
        "Dossier N", "Nom", "Categories", "Sous-categories", "Visa",
        "Montant honoraires (US $)", "Autres frais (US $)",
        "Montant facturé", "Total payé", "Solde restant", "Escrow"
    ]
    colonnes = [c for c in colonnes if c in df.columns]
    st.dataframe(df[colonnes], use_container_width=True)

    # ==============================
    # 🏆 Top 10
    # ==============================
    st.markdown("### 🏆 Top 10 des dossiers (par montant facturé)")
    top10 = df.nlargest(10, "Montant facturé")[["Nom", "Montant facturé", "Total payé", "Solde restant"]]
    st.dataframe(top10, use_container_width=True)
