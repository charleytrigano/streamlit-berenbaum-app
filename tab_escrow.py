import streamlit as st
import pandas as pd

def tab_escrow():
    """Onglet Escrow — suivi des dossiers en attente de règlement."""
    st.header("🛡️ Gestion des dossiers Escrow")

    # Vérifier que les données sont disponibles
    if "data_xlsx" not in st.session_state or not st.session_state["data_xlsx"]:
        st.warning("⚠️ Aucune donnée disponible. Chargez le fichier Excel via 📄 Fichiers.")
        return

    data = st.session_state["data_xlsx"]

    # Rechercher la feuille Escrow (insensible à la casse)
    escrow_key = None
    for key in data.keys():
        if key.strip().lower() == "escrow":
            escrow_key = key
            break

    if not escrow_key:
        st.warning("⚠️ Feuille Escrow non trouvée.")
        return

    df = data[escrow_key].copy()

    if df.empty:
        st.info("Aucun dossier en Escrow pour le moment.")
        return

    # Nettoyage et formatage
    def _to_float(x):
        try:
            s = str(x).replace(",", ".").replace("\u00A0", "").strip()
            return float(s) if s not in ["", "nan", "None"] else 0.0
        except:
            return 0.0

    if "Montant" in df.columns:
        df["Montant"] = df["Montant"].map(_to_float)

    st.subheader(f"📦 Dossiers en Escrow ({len(df)})")
    st.dataframe(df, use_container_width=True, height=350)

    # Calcul total
    total_escrow = df["Montant"].sum() if "Montant" in df.columns else 0.0
    st.metric("💰 Total Escrow", f"${total_escrow:,.2f}")

    st.markdown("---")

    # Gestion des actions
    st.subheader("📝 Mettre à jour l'état d'un dossier")
    dossier_id = st.text_input("Numéro de dossier à mettre à jour")
    new_state = st.selectbox("Nouvel état", ["", "En attente", "Réclamé", "Réglé"])

    if st.button("✅ Mettre à jour l'état"):
        if dossier_id and new_state:
            mask = df["Dossier N"].astype(str) == dossier_id
            if mask.any():
                df.loc[mask, "État"] = new_state
                if new_state == "Réclamé":
                    df.loc[mask, "Date réclamation"] = pd.Timestamp.now().strftime("%Y-%m-%d")
                data[escrow_key] = df
                st.session_state["data_xlsx"] = data
                st.success(f"✅ Dossier {dossier_id} mis à jour ({new_state}).")
            else:
                st.warning("Numéro de dossier introuvable.")

    st.markdown("---")

    st.subheader("📤 Exporter la liste Escrow")
    if st.button("💾 Télécharger au format Excel"):
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
