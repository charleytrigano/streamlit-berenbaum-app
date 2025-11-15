def format_kpi(value):
    if abs(value) >= 1_000_000:
        return f"{value/1_000_000:.1f}M"
    if abs(value) >= 1_000:
        return f"{value/1_000:.1f}k"
    return f"{value:,.0f}"

def tab_dashboard():
    st.header("📊 Dashboard")

    st.markdown(
        """
        <style>
        .stMetric .number { font-size: 1.2rem !important; }
        </style>
        """,
        unsafe_allow_html=True
    )

    # ... data loading ...

    # Dans l'affichage
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Nombre total de dossiers clients", format_kpi(total_clients))
    with col2:
        st.metric("Honoraires facturés (US $)", format_kpi(total_honoraires))
    with col3:
        st.metric("Total autres frais (US $)", format_kpi(total_autres_frais))
    # ... etc
