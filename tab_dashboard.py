import streamlit as st
import pandas as pd
from datetime import datetime

# ---------- Helpers de normalisation / mapping ----------
def _norm_cols(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    mapping_candidates = {
        "Visa": ["visa", "type visa", "type_de_visa", "type-visa"],
        "Catégorie": ["catégorie", "categorie", "catégorie ", "category"],
        "Sous-catégorie": ["sous-catégorie", "sous categorie", "sous-categorie", "subcategory"],
        "Année": ["année", "annee", "year"],
        "Mois": ["mois", "month"],
        "Montant honoraires (US $)": [
            "montant honoraires (us $)", "honoraires", "montant_honoraires_us", "montant honoraires"
        ],
        "Autres frais (US $)": [
            "autres frais (us $)", "autres_frais_us", "autres frais"
        ],
        "Acompte 1": ["acompte 1", "a1", "acompte1"],
        "Acompte 2": ["acompte 2", "a2", "acompte2"],
        "Acompte 3": ["acompte 3", "a3", "acompte3"],
        "Acompte 4": ["acompte 4", "a4", "acompte4"],
        "Nom": ["nom", "client", "full name", "name"],
        # dates potentielles pour déduire Année/Mois
        "_date_probe_": [
            "date", "date création", "date creation", "date d'envoi", "date envoi",
            "créé le", "created at", "created_on"
        ],
    }

    # indexer colonnes en minuscule -> original
    lower2orig = {c.strip().lower(): c for c in df.columns}
    def find_col(cands):
        for cand in cands:
            if cand in lower2orig:
                return lower2orig[cand]
        return None

    # appliquer mapping vers noms standards
    for target, cands in mapping_candidates.items():
        if target == "_date_probe_":
            continue
        if target not in df.columns:
            found = find_col([c.strip().lower() for c in cands])
            if found:
                df.rename(columns={found: target}, inplace=True)

    # garantir colonnes financières
    for col in [
        "Montant honoraires (US $)",
        "Autres frais (US $)",
        "Acompte 1", "Acompte 2", "Acompte 3", "Acompte 4"
    ]:
        if col not in df.columns:
            df[col] = 0

    # convertir numériques proprement
    for col in [
        "Montant honoraires (US $)",
        "Autres frais (US $)",
        "Acompte 1", "Acompte 2", "Acompte 3", "Acompte 4"
    ]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # construire Montant facturé / Payé / Solde
    df["Montant facturé"] = df["Montant honoraires (US $)"] + df["Autres frais (US $)"]
    df["Total payé"] = df[["Acompte 1", "Acompte 2", "Acompte 3", "Acompte 4"]].sum(axis=1)
    df["Solde restant"] = df["Montant facturé"] - df["Total payé"]

    # Visa: fallback depuis 'Type visa' déjà géré ci-dessus; si rien, créer vide pour éviter plantage filtres
    if "Visa" not in df.columns:
        df["Visa"] = ""

    # Année / Mois: si manquantes, tenter de les déduire d'une colonne date probable
    if ("Année" not in df.columns) or ("Mois" not in df.columns):
        # trouver une colonne date exploitable
        date_col = None
        for probe in mapping_candidates["_date_probe_"]:
            if probe in lower2orig:
                cand = lower2orig[probe]
                date_col = cand
                break
        if date_col is not None:
            # parse
            parsed = pd.to_datetime(df[date_col], errors="coerce", dayfirst=True, infer_datetime_format=True)
            if "Année" not in df.columns:
                df["Année"] = parsed.dt.year
            if "Mois" not in df.columns:
                # nom de mois (01..12 ou libellé FR). On garde libellé FR court.
                df["Mois"] = parsed.dt.month_name(locale="fr_FR").fillna(parsed.dt.month.astype("Int64").astype(str))
        else:
            # à défaut, créer colonnes vides pour ne pas casser les filtres
            if "Année" not in df.columns:
                df["Année"] = ""
            if "Mois" not in df.columns:
                df["Mois"] = ""

    # Catégorie / Sous-catégorie: si absentes, créer colonnes vides pour filtres
    if "Catégorie" not in df.columns:
        df["Catégorie"] = ""
    if "Sous-catégorie" not in df.columns:
        df["Sous-catégorie"] = ""

    return df


def tab_dashboard():
    """Tableau de bord principal - synthèse financière avec filtres robustes."""
    st.header("📊 Tableau de bord")

    # Vérifier si les données Excel sont chargées
    if "data_xlsx" not in st.session_state or not st.session_state["data_xlsx"]:
        st.warning("⚠️ Aucune donnée disponible. Chargez d'abord le fichier Excel via l'onglet '📄 Fichiers'.")
        return

    data = st.session_state["data_xlsx"]
    if "Clients" not in data:
        st.error("❌ La feuille 'Clients' est absente du fichier Excel.")
        return

    df_raw = data["Clients"]
    if df_raw.empty:
        st.warning("📄 La feuille 'Clients' est vide.")
        return

    # Normaliser / remapper / compléter
    df = _norm_cols(df_raw)

    # ================= FILTRES =================
    st.markdown("### 🎯 Filtres")
    col1, col2, col3, col4, col5 = st.columns(5)

    def _opts(dfcol, all_label="(Tous)"):
        if dfcol not in df.columns:
            return [all_label]
        vals = sorted([v for v in df[dfcol].dropna().unique().tolist() if str(v).strip() != ""])
        return [all_label] + vals if vals else [all_label]

    categorie = col1.selectbox("Catégorie", _opts("Catégorie", "(Toutes)"), key="dash_cat")
    souscat   = col2.selectbox("Sous-catégorie", _opts("Sous-catégorie", "(Toutes)"), key="dash_souscat")
    visa      = col3.selectbox("Visa", _opts("Visa", "(Tous)"), key="dash_visa")
    annee     = col4.selectbox("Année", _opts("Année", "(Toutes)"), key="dash_annee")
    mois      = col5.selectbox("Mois", _opts("Mois", "(Tous)"), key="dash_mois")

    # Application des filtres (uniquement si valeur choisie ≠ (Tous/Toutes))
    if categorie != "(Toutes)":
        df = df[df["Catégorie"] == categorie]
    if souscat != "(Toutes)":
        df = df[df["Sous-catégorie"] == souscat]
    if visa != "(Tous)":
        df = df[df["Visa"] == visa]
    if annee != "(Toutes)":
        df = df[df["Année"].astype(str) == str(annee)]
    if mois != "(Tous)":
        df = df[df["Mois"].astype(str) == str(mois)]

    st.markdown("---")

    # ================= SYNTHÈSE FINANCIÈRE =================
    st.subheader("📊 Synthèse financière")
    total_honoraire = df["Montant honoraires (US $)"].sum()
    total_autres    = df["Autres frais (US $)"].sum()
    total_facture   = df["Montant facturé"].sum()
    total_paye      = df["Total payé"].sum()
    total_solde     = df["Solde restant"].sum()

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Honoraires", f"{total_honoraire:,.0f} $")
    c2.metric("Autres frais", f"{total_autres:,.0f} $")
    c3.metric("Facturé", f"{total_facture:,.0f} $")
    c4.metric("Payé", f"{total_paye:,.0f} $")
    c5.metric("Solde", f"{total_solde:,.0f} $")

    st.markdown("---")

    # ================= TABLEAU DES CLIENTS =================
    st.subheader("📋 Dossiers clients")
    colonnes_aff = [
        "Nom", "Visa",
        "Montant honoraires (US $)", "Autres frais (US $)",
        "Montant facturé", "Total payé", "Solde restant",
        "Catégorie", "Sous-catégorie", "Année", "Mois"
    ]
    cols_exist = [c for c in colonnes_aff if c in df.columns]
    df_view = df[cols_exist].copy()

    # formatage numérique sécurisé
    numeric_cols = df_view.select_dtypes(include=["number"]).columns
    st.dataframe(
        df_view.style.format(subset=numeric_cols, formatter="{:,.2f}"),
        use_container_width=True,
        height=420,
    )

    st.markdown("---")

    # ================= TOP 10 CLIENTS =================
    st.subheader("🏆 Top 10 des dossiers (par montant facturé)")
    if "Montant facturé" in df.columns:
        top10 = df.nlargest(10, "Montant facturé")[
            [c for c in ["Nom", "Visa", "Montant facturé", "Total payé", "Solde restant"] if c in df.columns]
        ]
        num_top = top10.select_dtypes(include=["number"]).columns
        st.dataframe(
            top10.style.format(subset=num_top, formatter="{:,.2f}"),
            use_container_width=True,
            height=380,
        )
    else:
        st.info("Colonne 'Montant facturé' absente : impossible d'afficher le Top 10.")
