import streamlit as st
import pandas as pd

def tab_dashboard():
    """Tableau de bord principal - synthèse financière + Escrow."""
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

    # Conversion propre des nombres
    def _to_float(x):
        try:
            s = str(x).replace(",", ".").replace("\u00A0", "").strip()
            return float(s) if s not in ["", "nan", "None"] else 0.0
        except:
            return 0.0

    for col in ["Montant honoraires (US $)", "Autres frais (US $)", "Acompte 1", "Acompte 2", "Acompte 3", "Acompte 4"]:
        if col in df.columns:
            df[col] = df[col].map(_to_float)
        else:
            df[col] = 0.0

    # ==============================
    # 🔍 Filtres
    # ==============================
    st.subheader("🎛️ Filtres")
    c1, c2, c3 = st.columns(3)
    cat = c1.selectbox("Catégorie", ["(Toutes)"] + sorted(df["Categories"].dropna().unique().tolist()) if "Categories" in df else ["(Toutes)"])
    souscat = c2.selectbox("Sous-catégorie", ["(Toutes)"] + sorted(df["Sous-categories"].dropna().unique().tolist()) if "Sous-categories" in df else ["(Toutes)"])
    visa = c3.selectbox("Visa", ["(Tous)"] + sorted(df["Visa"].dropna().unique().tolist()) if "Visa" in df else ["(Tous)"])

    if cat != "(Toutes)":
        df = df[df["Categories"] == cat]
    if souscat != "(Toutes)":
        df = df[df["Sous-categories"] == souscat]
    if visa != "(Tous)":
        df = df[df["Visa"] == visa]

    # ==============================
    # 💰 Calculs Clients
    # ==============================
    df["Montant facturé"] = df["Montant honoraires (US $)"] + df["Autres frais (US $)"]
    df["Total payé"] = df["Acompte 1"] + df["Acompte 2"] + df["Acompte 3"] + df["Acompte 4"]
    df["Solde restant"] = df["Montant facturé"] - df["Total payé"]

    montant_facture = df["Montant facturé"].sum()
    montant_paye = df["Total payé"].sum()
    solde_restant = df["Solde restant"].sum()
    n_dossiers = len(df)

    # ==============================
    # 🛡️ Lecture Escrow
    # ==============================
    escrow_count = 0
    escrow_total = 0.0
    escrow_key = None

    # Recherche de la feuille "Escrow" (insensible à la casse)
    for key in data.keys():
        if key.strip().lower() == "escrow":
            escrow_key = key
            break

    if escrow_key:
        escrow_df = data[escrow_key].copy()
        if not escrow_df.empty:
            escrow_count = len(escrow_df)
            if "Montant" in escrow_df.columns:
                escrow_total = escrow_df["Montant"].map(_to_float).sum()

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
    # 🏆 Top 10 Dossiers
    # ==============================
    st.markdown("### 🏆 Top 10 des dossiers (par montant facturé)")
    top10 = df.nlargest(10, "Montant facturé")[["Nom", "Montant facturé", "Total payé", "Solde restant"]]
    st.dataframe(top10, use_container_width=True)
