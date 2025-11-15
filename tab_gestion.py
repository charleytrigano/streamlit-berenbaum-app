# ... imports et début inchangés

def tab_gestion():
    st.header("✏️ / 🗑️ Gestion d’un dossier")
    data = ensure_loaded()
    if data is None or "Clients" not in data or data["Clients"].empty:
        st.warning("Aucun fichier ou dossier valide.")
        return
    df = data["Clients"]

    # Choix entre numéro ou nom
    mode_selection = st.radio("Type de sélection", ["Par numéro de dossier", "Par nom"])
    if mode_selection == "Par numéro de dossier":
        dossier_list = pd.to_numeric(df["Dossier N"], errors="coerce").dropna().astype(str).tolist()
        selected = st.selectbox("Choisir un Dossier N", dossier_list)
        mask = df["Dossier N"].astype(str) == selected
    else:
        nom_list = df["Nom"].dropna().astype(str).unique().tolist()
        selected = st.selectbox("Choisir un client par nom", nom_list)
        mask = df["Nom"].astype(str) == selected

    if not mask.any():
        st.error("Dossier introuvable.")
        return

    dossier = df[mask].iloc[0]

    # ... suite inchangée jusqu'à la section acompte 1 ...

    # Section Paiements Restants (Dynamic)
    st.subheader("💳 Paiements complémentaires")
    max_payments = 5  # nombre max de paiements
    for n in range(2, max_payments+1):
        acompte_col = f"Acompte {n}"
        date_col = f"Date Acompte {n}"
        if acompte_col not in df.columns:
            df[acompte_col] = 0.0
        if date_col not in df.columns:
            df[date_col] = ""

        colA, colB = st.columns(2)
        with colA:
            acompte_val = st.number_input(
                f"{acompte_col} (US $)",
                min_value=0.0,
                value=_to_float(dossier.get(acompte_col, 0.0)),
                step=10.0,
                key=f"acompte_{n}"
            )
        with colB:
            date_val = st.date_input(
                f"{date_col}",
                _to_date(dossier.get(date_col), default=None),
                key=f"date_acompte_{n}"
            )

    # ... puis dans 'Enregistrer les modifications', sauvegarder aussi ces champs:
    # Exemple :
    for n in range(2, max_payments+1):
        acompte_col = f"Acompte {n}"
        date_col = f"Date Acompte {n}"
        df.loc[df[mask].index[0], acompte_col] = st.session_state.get(f"acompte_{n}", 0.0)
        df.loc[df[mask].index[0], date_col] = pd.to_datetime(st.session_state.get(f"date_acompte_{n}", None))

    # ... puis sauvegarde comme avant
