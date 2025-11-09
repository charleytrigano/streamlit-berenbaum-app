import streamlit as st
import pandas as pd

def tab_escrow():
    """Onglet Escrow — suivi des dossiers en attente de règlement."""
    st.header("🛡️ Gestion des dossiers Escrow")

    # Vérifie la présence des données en mémoire
    if "data_xlsx" not in st.session_state or not st.session_state["data_xlsx"]:
        st.warning("⚠️ Aucune donnée disponible. Chargez le fichier Excel via 📄 Fichiers.")
        return

    data = st.session_state["data_xlsx"]

    # Recherche intelligente de la feuille Escrow
    escrow_key = None
    for key in data.keys():
        if "escrow" in key.strip().lower():
            escrow_key = key
            break

    if not escrow_key:
        st.warning("⚠️ Aucune feuille 'Escrow' trouvée dans le fichier Excel.")
        return

    df = data[escrow_key]
    if isinstance(df, dict):
        df = pd.DataFrame(df)

    if df.empty:
        st.info("📭 Aucun dossier en Escrow actuellement.")
        return

    # Nettoyage et conversion des montants
    def _to_float(x):
        try:
            s = str(x).replace(",", ".").replace("\u00A0", "").strip()
            return float(s) if s not in ["", "nan", "None"] else 0.0
        except:
            return 0.0

    if "Montant" in df.columns:
        df["Montant"] = df["Montant"].map(_to_float)
    else:
        df["Montant"] = 0.0

    # === Recalcul KPI ===
    nb_dossiers = len(df)
    total_escrow = df["Montant"].sum()

    def _fmt_money(v):
        return f"{v:,.2f}".replace(",", " ").replace(".", ",") + " $"

    st.markdown("### 📊 Synthèse Escrow")
    c1, c2 = st.columns(2)
    c1.metric("📦 Dossiers en Escrow", f"{nb_dossiers:,}".replace(",", " "))
    c2.metric("💰 Montant total", _fmt_money(total_escrow))

    st.markdown("---")

    # === Tableau principal ===
    st.subheader("📋 Liste des dossiers en Escrow")
    df_display = df.copy()
    df_display["Montant"] = df_display["Montant"].map(_fmt_money)
    st.dataframe(df_display, use_container_width=True, height=400)

    # === Mise à jour dossier ===
    st.markdown("---")
    st.subheader("📝 Mettre à jour l'état d'un dossier")

    dossier_id = st.text_input("Numéro de dossier à modifier", key="escrow_dossier_id")
    new_state = st.selectbox("Nouvel état", ["", "En attente", "Réclamé", "Réglé"], key="escrow_new_state")

    if st.button("✅ Enregistrer la modification", key="escrow_save_btn"):
        if dossier_id and new_state:
            mask = df["Dossier N"].astype(str) == dossier_id
            if mask.any():
                df.loc[mask, "État"] = new_state
                if new_state == "Réclamé":
                    df.loc[mask, "Date réclamation"] = pd.Timestamp.now().strftime("%Y-%m-%d")
                # ✅ Mise à jour en mémoire
                data[escrow_key] = df
                st.session_state["data_xlsx"] = data
                st.success(f"Dossier {dossier_id} mis à jour ({new_state}).")
                st.rerun()  # 🔄 Force la mise à jour immédiate des KPI
            else:
                st.warning("Numéro de dossier introuvable.")

    # === Export Excel ===
    st.markdown("---")
    st.subheader("📤 Exporter la liste Escrow")

    if st.button("💾 Télécharger au format Excel", key="escrow_export_btn"):
        from io import BytesIO
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Escrow")
        st.download_button(
            label="⬇️ Télécharger Escrow.xlsx",
            data=buffer.getvalue(),
            file_name="Escrow.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
