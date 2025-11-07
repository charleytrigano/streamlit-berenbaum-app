import streamlit as st
import pandas as pd
import re

def _clean_number_series(s: pd.Series) -> pd.Series:
    """
    Convertit une série (montants en texte) en float de manière robuste.
    - supprime $ US, espaces (y compris insécables), lettres
    - gère 1,234.56 (US) et 1.234,56 (EU) et 1 234,56
    - gère les parenthèses pour négatif: (123,45) -> -123,45
    - remplace NaN/vides par 0.0
    """
    if s is None:
        return pd.Series(dtype=float)

    s = s.astype(str)

    # marquer les négatifs avec parenthèses
    neg_mask = s.str.contains(r"^\s*\(.*\)\s*$")

    # uniformiser espaces
    s = (
        s.str.replace("\u202f", "", regex=False)  # fine NBSP
         .str.replace("\xa0", "", regex=False)    # NBSP
         .str.replace(" ", "", regex=False)
    )

    # enlever symboles monétaires et lettres, mais garder . , - et chiffres
    s = s.str.replace(r"[^\d\-,\.]", "", regex=True)

    # normaliser séparateurs:
    # - si contient à la fois '.' et ',' => on suppose format US: 1,234.56 -> enlever les virgules
    # - sinon si seulement ',', on suppose virgule décimale: 1234,56 -> remplacer par '.'
    both = s.str.contains(r"\.") & s.str.contains(r",")
    s = s.where(~both, s.str.replace(",", "", regex=False))

    only_comma = s.str.contains(r",") & ~both
    s = s.where(~only_comma, s.str.replace(",", ".", regex=False))

    # vider les chaînes vides -> "0"
    s = s.replace("", "0")

    # conversion
    out = pd.to_numeric(s, errors="coerce").fillna(0.0)

    # appliquer le signe négatif si parenthèses
    out = out.where(~neg_mask, -out)

    return out

def _ensure_cols(df: pd.DataFrame, cols) -> pd.DataFrame:
    for c in cols:
        if c not in df.columns:
            df[c] = 0.0
    return df

def main():
    st.header("📊 Tableau de bord")

    df_src = st.session_state.get("clients_df")
    if df_src is None or df_src.empty:
        st.warning("Aucune donnée disponible. Chargez un fichier dans l’onglet 📄 Fichiers.")
        return

    # colonnes attendues
    COL_HONO = "Montant honoraires (US $)"
    COL_AUTRES = "Autres frais (US $)"
    AC_COLS = ["Acompte 1", "Acompte 2", "Acompte 3", "Acompte 4"]

    # dupliquer pour calculs
    df = df_src.copy()

    # s'assurer que les colonnes existent (sinon colonnes 0.0)
    needed = [COL_HONO, COL_AUTRES] + AC_COLS
    df = _ensure_cols(df, needed)

    # nettoyer/converter en float de manière robuste
    df[COL_HONO]  = _clean_number_series(df[COL_HONO])
    df[COL_AUTRES]= _clean_number_series(df[COL_AUTRES])
    for c in AC_COLS:
        df[c] = _clean_number_series(df[c])

    # calculs
    df["Montant facturé"] = df[COL_HONO] + df[COL_AUTRES]
    df["Total payé"] = df[AC_COLS].sum(axis=1)
    df["Solde restant"] = df["Montant facturé"] - df["Total payé"]

    # agrégats GLOBAUX (sur TOUT le fichier)
    total_clients = int(len(df))
    total_facture = float(df["Montant facturé"].sum())
    total_paye = float(df["Total payé"].sum())
    solde_restant = float(df["Solde restant"].sum())

    # KPIs compacts sur une ligne
    st.markdown("### 📈 Indicateurs financiers")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("👥 Clients", f"{total_clients}")
    c2.metric("💰 Montant facturé", f"{total_facture:,.2f} US$")
    c3.metric("💵 Total payé", f"{total_paye:,.2f} US$")
    c4.metric("🧾 Solde restant", f"{solde_restant:,.2f} US$")

    st.markdown("---")

    # tableau COMPLET (pas seulement 10 lignes)
    st.subheader("📋 Liste complète des dossiers")
    cols_show = ["Nom", COL_HONO, COL_AUTRES, "Montant facturé", "Total payé", "Solde restant"]
    # si "Nom" absent, on n’empêche pas l’affichage
    cols_show = [c for c in cols_show if c in df.columns]
    st.dataframe(df[cols_show], use_container_width=True, hide_index=True)

    st.markdown("### 📊 Top 10 par montant facturé")
    top10 = df.nlargest(10, "Montant facturé")
    if "Nom" in top10.columns:
        st.bar_chart(top10.set_index("Nom")["Montant facturé"])
    else:
        st.bar_chart(top10["Montant facturé"])
