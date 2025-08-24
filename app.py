from __future__ import annotations

import streamlit as st

from db_utils import get_engine, load_dims, load_distincts, execute_query
from filters import render_filters, build_params
import charts


def main() -> None:
    """Main function for the dashboard."""
    st.set_page_config(
        page_title="Clickstream Purchase Intent Dashboard",
        page_icon="🛒",
        layout="wide",
    )

    # Initialise database engine
    engine = get_engine()

    # Load dimension labels and distinct filter values
    dims = load_dims(engine)
    distincts = load_distincts(engine)

    # If either dims or distincts failed to load, abort early
    if not dims or not distincts:
        st.sidebar.error("Could not load filter data from the database.")
        st.stop()

    # Render sidebar filters and capture their configuration
    filter_config = render_filters(dims, distincts)

    # Build KPI parameters and fetch KPI data
    func_call_template = "SELECT * FROM clickstream.%(func_name)s(:p_months, :p_visitor_types, :p_weekend, :p_browsers, :p_os, :p_regions, :p_traffics, :p_page_types)"
    kpi_params = build_params(filter_config, target_graph='kpi')
    kpi_df = execute_query(engine, func_call_template % {'func_name': 'get_kpis'}, kpi_params)

    # Title and caption
    st.title("🛒 Clickstream Purchase Intent Dashboard")
    st.caption("Live from PostgreSQL Functions · filter in the sidebar to slice the insights.")

    # Display KPIs
    charts.plot_kpis(kpi_df)
    st.divider()
    if kpi_df.empty and any(p for p in kpi_params.values()):
        st.warning("No data for the current KPI filters. Try widening your selection.")

    # Fetch and display individual charts
    # Weekday vs Weekend
    wvw_params = build_params(filter_config, target_graph='weekend')
    wvw_df = execute_query(engine, func_call_template % {'func_name': 'get_weekday_vs_weekend'}, wvw_params)
    st.subheader("Weekday vs Weekend")
    charts.plot_weekday_vs_weekend(wvw_df)

    # Monthwise Conversion Rate
    mrev_params = build_params(filter_config, target_graph='month')
    mrev_df = execute_query(engine, func_call_template % {'func_name': 'get_monthwise_revenue'}, mrev_params)
    st.subheader("Monthwise Conversion Rate")
    charts.plot_monthwise_conversion_rate(mrev_df)

    # Browser performance – share and conversion
    brows_params = build_params(filter_config, target_graph='browser')
    brows_df = execute_query(engine, func_call_template % {'func_name': 'get_browser_performance'}, brows_params)
    col1, col2 = st.columns(2, gap="large")
    with col1:
        st.subheader("Browser Share (by Sessions)")
        charts.plot_browser_share(brows_df)
    with col2:
        st.subheader("Browser Conversion Rate")
        charts.plot_browser_conversion_rate(brows_df)

    # Traffic type performance and Region performance
    traf_params = build_params(filter_config, target_graph='traffic')
    traf_df = execute_query(engine, func_call_template % {'func_name': 'get_traffic_type_performance'}, traf_params)
    reg_params = build_params(filter_config, target_graph='region')
    reg_df = execute_query(engine, func_call_template % {'func_name': 'get_region_performance'}, reg_params)
    col3, col4 = st.columns(2, gap="large")
    with col3:
        st.subheader("Traffic Type – Conversion Rate")
        charts.plot_traffic_type_performance(traf_df)
    with col4:
        st.subheader("Region – Conversion Rate")
        charts.plot_region_performance(reg_df)

    # OS performance
    st.subheader("OS Performance")
    os_params = build_params(filter_config, target_graph='os')
    os_df = execute_query(engine, func_call_template % {'func_name': 'get_os_performance'}, os_params)
    charts.plot_os_performance(os_df)

    # Page type performance
    st.subheader("Page Type Performance")
    page_params = build_params(filter_config, target_graph='page_type')
    page_df = execute_query(engine, func_call_template % {'func_name': 'get_page_type_performance'}, page_params)
    charts.plot_page_type_performance(page_df)

    # Engagement metrics impact
    st.subheader("Engagement Metrics Impact")
    eng_params = build_params(filter_config, target_graph='engagement')
    eng_df = execute_query(engine, func_call_template % {'func_name': 'get_engagement_metrics_impact'}, eng_params)
    charts.plot_engagement_metrics_impact(eng_df)

    # Special day effect
    st.subheader("Special Day Effect")
    sp_params = build_params(filter_config, target_graph='special_day')
    sp_df = execute_query(engine, func_call_template % {'func_name': 'get_special_day_effect'}, sp_params)
    charts.plot_special_day_effect(sp_df)

    # Cohort-style views derived from SQL views
    st.subheader("Monthly New vs Returning Visitors")
    mnvr_df = execute_query(engine, "SELECT * FROM clickstream.monthly_new_vs_returning")
    charts.plot_monthly_new_vs_returning(mnvr_df)

    st.subheader("Weekday Conversion by Traffic")
    wct_df = execute_query(engine, "SELECT * FROM clickstream.weekday_conversion_by_traffic")
    charts.plot_weekday_conversion_by_traffic(wct_df)

    st.subheader("Browser × OS Conversion Matrix")
    bos_df = execute_query(engine, "SELECT * FROM clickstream.browser_os_conversion_matrix")
    charts.plot_browser_os_matrix(bos_df)

    # Divider before cohort analysis
    st.divider()
    # Cohort Analysis section with selectable view and table display
    st.header("Cohort Analysis")
    cohort_view_choice = st.selectbox(
        "Select a Cohort View",
        [
            "Monthly New vs. Returning Visitors",
            "Weekday Conversion by Traffic",
            "Browser vs. OS Conversion Matrix",
        ],
    )
    if cohort_view_choice == "Monthly New vs. Returning Visitors":
        df_cohort = execute_query(engine, "SELECT * FROM clickstream.monthly_new_vs_returning")
        charts.plot_monthly_new_vs_returning(df_cohort)
        st.dataframe(df_cohort, use_container_width=True)
    elif cohort_view_choice == "Weekday Conversion by Traffic":
        df_cohort = execute_query(engine, "SELECT * FROM clickstream.weekday_conversion_by_traffic")
        charts.plot_weekday_conversion_by_traffic(df_cohort)
        st.dataframe(df_cohort, use_container_width=True)
    else:
        df_cohort = execute_query(engine, "SELECT * FROM clickstream.browser_os_conversion_matrix")
        charts.plot_browser_os_matrix(df_cohort)
        st.dataframe(df_cohort, use_container_width=True)

    st.caption("Data source: Logic executed in PostgreSQL Functions and Views.")


if __name__ == "__main__":
    main()