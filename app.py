import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine, text

st.set_page_config(page_title="Clickstream Purchase Intent Dashboard", page_icon="🛒", layout="wide")

# -----------------------------
# DB CONNECTION
# -----------------------------
def get_engine():
    s = st.secrets["postgres"]
    url = f'postgresql+psycopg2://{s["user"]}:{s["password"]}@{s["host"]}:{s["port"]}/{s["dbname"]}'
    return create_engine(url, pool_pre_ping=True)

def df_query(sql: str, params: dict | None = None) -> pd.DataFrame:
    with get_engine().begin() as con:
        return pd.read_sql(text(sql), con, params=params or {})

# -----------------------------
# DISTINCTS FROM VIEWS (SQL-first)
# -----------------------------
@st.cache_data(ttl=300, show_spinner=False)
def load_distincts_from_views():
    d = {}
    with get_engine().begin() as con:
        # months
        d["month"] = pd.read_sql(text("SELECT DISTINCT month FROM clickstream.monthwise_revenue ORDER BY month"), con)["month"].tolist()
        # visitor types
        d["visitortype"] = pd.read_sql(text("SELECT DISTINCT visitortype FROM clickstream.conversion_rates ORDER BY visitortype"), con)["visitortype"].tolist()
        # weekend exists in multiple views; we'll just set labels here
        d["weekend_labels"] = ["All", "Weekday only", "Weekend only"]
        # browser names (as exposed by your view)
        d["browser"] = pd.read_sql(text("SELECT DISTINCT browser FROM clickstream.browser_usage ORDER BY browser"), con)["browser"].tolist()
        # traffic types (labels as exposed by your view)
        d["traffictype"] = pd.read_sql(text("SELECT DISTINCT traffictype FROM clickstream.traffic_type_performance ORDER BY traffictype"), con)["traffictype"].tolist()
        # regions (labels as exposed by your view)
        d["region"] = pd.read_sql(text("SELECT DISTINCT region FROM clickstream.region_performance ORDER BY region"), con)["region"].tolist()
        d["os"] = pd.read_sql(text("SELECT DISTINCT os_name FROM clickstream.os_performance ORDER BY os_name"),con)["os_name"].tolist()
    return d

# -----------------------------
# UI — FILTERS
# -----------------------------
st.sidebar.title("Filters (apply where relevant)")
distincts = load_distincts_from_views()

month_f      = st.sidebar.multiselect("Month (Monthwise)", options=distincts["month"])
visit_f      = st.sidebar.multiselect("Visitor Type (VisitorType × Weekend)", options=distincts["visitortype"])
weekend_opt  = st.sidebar.selectbox("Weekend (Overview/VisitorType)", options=distincts["weekend_labels"], index=0)

browser_f    = st.sidebar.multiselect("Browser (Channels)", options=distincts["browser"])
traffic_f    = st.sidebar.multiselect("Traffic Type (Channels)", options=distincts["traffictype"])
region_f     = st.sidebar.multiselect("Region (Geography)", options=distincts["region"])

if st.sidebar.button("🔄 Reset filters"):
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    st.rerun()

# -----------------------------
# KPI — executive_summary
# -----------------------------
st.title("🛒 Clickstream Purchase Intent Dashboard")
st.caption("SQL‑first: All metrics come from PostgreSQL *views*; Streamlit just visualizes them.")

exec_df = df_query("SELECT total_sessions, total_conversions, overall_conversion_rate FROM clickstream.executive_summary")
if exec_df.empty:
    st.error("Executive summary returned no data.")
    st.stop()

k1, k2, k3 = st.columns(3)
k1.metric("Total Sessions", f"{int(exec_df.loc[0,'total_sessions']):,}")
k2.metric("Total Conversions", f"{int(exec_df.loc[0,'total_conversions']):,}")
k3.metric("Overall Conversion Rate", f"{float(exec_df.loc[0,'overall_conversion_rate']):.2f}%")

st.divider()
dbg = st.expander("🛠 SQL Debug (last queries)")

# -----------------------------
# TABS
# -----------------------------
tab_overview, tab_channels, tab_engagement, tab_geo = st.tabs(
    ["Overview", "Channels", "Engagement", "Geography"]
)

# ================== OVERVIEW ==================
with tab_overview:
    c1, c2 = st.columns(2, gap="large")

    # Weekday vs Weekend
    wvw_where = ""
    if weekend_opt == "Weekday only":
        wvw_where = "WHERE weekend = false"
    elif weekend_opt == "Weekend only":
        wvw_where = "WHERE weekend = true"

    sql_wvw = f"""
        SELECT weekend, total_sessions, conversions, conversion_rate
        FROM clickstream.weekday_vs_weekend
        {wvw_where}
        ORDER BY weekend
    """
    wvw = df_query(sql_wvw)
    with dbg: st.code(sql_wvw, language="sql")

    if not wvw.empty:
        wvw["weekend"] = wvw["weekend"].map({True: "Weekend", False: "Weekday"})
        with c1:
            st.subheader("Weekday vs Weekend")
            fig = px.bar(wvw, x="weekend", y="conversion_rate", text="conversion_rate",
                         labels={"weekend": "", "conversion_rate": "Conversion Rate (%)"})
            fig.update_traces(texttemplate="%{text:.2f}%")
            st.plotly_chart(fig, use_container_width=True)

    # Monthwise Conversion Rate
    m_params = {}
    m_where = ""
    if month_f:
        m_where = "WHERE month = ANY(:months)"
        m_params["months"] = month_f

    sql_month = f"""
        SELECT month, total_sessions, conversions, conversion_rate
        FROM clickstream.monthwise_revenue
        {m_where}
        ORDER BY month
    """
    mrev = df_query(sql_month, m_params)
    with dbg:
        st.code(sql_month, language="sql")
        if m_params: st.json(m_params)

    with c2:
        st.subheader("Monthwise Conversion Rate")
        if not mrev.empty:
            fig = px.line(mrev, x="month", y="conversion_rate", markers=True,
                          labels={"month": "Month", "conversion_rate": "Conversion Rate (%)"})
            st.plotly_chart(fig, use_container_width=True)

    # Visitor Type × Weekend
    v_where_parts, v_params = [], {}
    if visit_f:
        v_where_parts.append("visitortype = ANY(:visit)")
        v_params["visit"] = visit_f
    if weekend_opt == "Weekday only":
        v_where_parts.append("weekend = false")
    elif weekend_opt == "Weekend only":
        v_where_parts.append("weekend = true")
    v_where = "WHERE " + " AND ".join(v_where_parts) if v_where_parts else ""

    sql_conv = f"""
        SELECT visitortype, weekend, conversion_rate
        FROM clickstream.conversion_rates
        {v_where}
        ORDER BY visitortype, weekend
    """
    vtw = df_query(sql_conv, v_params)
    with dbg:
        st.code(sql_conv, language="sql")
        if v_params: st.json(v_params)

    st.subheader("Visitor Type × Weekend")
    if not vtw.empty:
        vtw["weekend_label"] = vtw["weekend"].map({True: "Weekend", False: "Weekday"})
        fig = px.bar(vtw, x="visitortype", y="conversion_rate", color="weekend_label",
                     barmode="group",
                     labels={"visitortype": "Visitor Type", "conversion_rate": "Conversion Rate (%)", "weekend_label": ""},
                     text="conversion_rate")
        fig.update_traces(texttemplate="%{text:.2f}%")
        st.plotly_chart(fig, use_container_width=True)

    # Special Day Effect
    st.subheader("Special Day Effect")
    sql_sp = "SELECT specialday, total_sessions, conversions, conversion_rate FROM clickstream.special_day_effect ORDER BY specialday"
    sp = df_query(sql_sp)
    with dbg: st.code(sql_sp, language="sql")
    if not sp.empty:
        fig = px.bar(sp, x="specialday", y="conversion_rate",
                     labels={"specialday": "Special Day Score", "conversion_rate": "Conversion Rate (%)"},
                     text="conversion_rate")
        fig.update_traces(texttemplate="%{text:.2f}%")
        st.plotly_chart(fig, use_container_width=True)

# ================== CHANNELS ==================
with tab_channels:
    c3, c4 = st.columns(2, gap="large")

    # Browser Usage
    b_where, b_params = "", {}
    if browser_f:
        b_where = "WHERE browser = ANY(:browsers)"
        b_params["browsers"] = browser_f

    sql_brows = f"""
        SELECT browser, total_sessions, conversions, conversion_rate
        FROM clickstream.browser_usage
        {b_where}
        ORDER BY total_sessions DESC
    """
    brows = df_query(sql_brows, b_params)
    with dbg:
        st.code(sql_brows, language="sql")
        if b_params: st.json(b_params)

    with c3:
        st.subheader("Browser Share (by Sessions)")
        if not brows.empty:
            fig = px.pie(brows, names="browser", values="total_sessions", hole=0.45)
            st.plotly_chart(fig, use_container_width=True)

            fig = px.bar(brows, x="browser", y="conversion_rate",
                         labels={"browser": "Browser", "conversion_rate": "Conversion Rate (%)"},
                         text="conversion_rate")
            fig.update_traces(texttemplate="%{text:.2f}%")
            st.plotly_chart(fig, use_container_width=True)

    # Traffic Type Performance
    t_where, t_params = "", {}
    if traffic_f:
        t_where = "WHERE traffictype = ANY(:tt)"
        t_params["tt"] = traffic_f

    sql_traf = f"""
        SELECT traffictype, total_sessions, conversions, conversion_rate
        FROM clickstream.traffic_type_performance
        {t_where}
        ORDER BY conversion_rate DESC, total_sessions DESC
    """
    traf = df_query(sql_traf, t_params)
    with dbg:
        st.code(sql_traf, language="sql")
        if t_params: st.json(t_params)

    with c4:
        st.subheader("Traffic Type – Conversion Rate")
        if not traf.empty:
            fig = px.bar(traf, y="traffictype", x="conversion_rate", orientation="h",
                         labels={"traffictype": "Traffic Type", "conversion_rate": "Conversion Rate (%)"},
                         text="conversion_rate")
            fig.update_traces(texttemplate="%{text:.2f}%")
            st.plotly_chart(fig, use_container_width=True)
        # ----- Operating System Performance (optional) -----
    os_where, os_params = "", {}
    if 'os_f' not in st.session_state:
        # create a persistent key if needed
        st.session_state['os_f'] = []
    os_f = st.sidebar.multiselect("Operating System (Channels)", options=distincts.get("os", []), key='os_f')

    if os_f:
        os_where = "WHERE os_name = ANY(:oses)"
        os_params["oses"] = os_f

    sql_os = f"""
        SELECT os_name, total_sessions, conversions, conversion_rate
        FROM clickstream.os_performance
        {os_where}
        ORDER BY total_sessions DESC
    """
    osdf = df_query(sql_os, os_params)
    with dbg:
        st.code(sql_os, language="sql")
        if os_params: st.json(os_params)

    st.subheader("Operating System – Sessions & Conversion")
    if not osdf.empty:
        os_c1, os_c2 = st.columns(2, gap="large")
        with os_c1:
            fig = px.pie(osdf, names="os_name", values="total_sessions", hole=0.45)
            st.plotly_chart(fig, use_container_width=True)
        with os_c2:
            fig = px.bar(osdf, x="os_name", y="conversion_rate",
                         labels={"os_name":"OS","conversion_rate":"Conversion Rate (%)"},
                         text="conversion_rate")
            fig.update_traces(texttemplate="%{text:.2f}%")
            st.plotly_chart(fig, use_container_width=True)

            


# ================== ENGAGEMENT ==================
with tab_engagement:
    st.subheader("Page Type Performance (Avg pages & time by purchase outcome)")

    # Try tidy view first; fall back to wide view
    tried_sql = []
    sql_page_tidy = "SELECT revenue, page_type, avg_pages, avg_seconds FROM clickstream.page_type_performance_tidy ORDER BY revenue DESC, page_type"
    tried_sql.append(sql_page_tidy)
    try:
        pt = df_query(sql_page_tidy)
        used_tidy = not pt.empty
    except Exception:
        used_tidy = False

    if not used_tidy:
        sql_page_wide = """
            SELECT revenue,
                   avg_admin_pages,    avg_info_pages,    avg_product_pages,
                   avg_admin_duration, avg_info_duration, avg_product_duration
            FROM clickstream.page_type_performance
            ORDER BY revenue DESC
        """
        tried_sql.append(sql_page_wide)
        base = df_query(sql_page_wide)

        # Reshape wide -> tidy so charts are consistent
        pages = base.rename(columns={
            "avg_admin_pages": "administrative",
            "avg_info_pages": "informational",
            "avg_product_pages": "productrelated",
        }).melt(id_vars="revenue",
                value_vars=["administrative","informational","productrelated"],
                var_name="page_type", value_name="avg_pages")

        dur = base.rename(columns={
            "avg_admin_duration": "administrative",
            "avg_info_duration": "informational",
            "avg_product_duration": "productrelated",
        }).melt(id_vars="revenue",
                value_vars=["administrative","informational","productrelated"],
                var_name="page_type", value_name="avg_seconds")

        pt = pages.merge(dur, on=["revenue","page_type"], how="inner")
        used_tidy = True  # we now have tidy data

    # Show the queries we attempted
    with dbg:
        for s in tried_sql:
            st.code(s.strip(), language="sql")

    if pt.empty:
        st.info("Page type performance view returned no data.")
    else:
        pt["revenue_label"] = pt["revenue"].map({True: "Purchased", False: "No Purchase"})
        all_page_types = sorted(pt["page_type"].unique().tolist())
        all_outcomes   = ["Purchased", "No Purchase"]

        fcol1, fcol2, fcol3 = st.columns([1,1,1])
        with fcol1:
            selected_pages = st.multiselect("Page Type", options=all_page_types, default=all_page_types)
        with fcol2:
            selected_outcomes = st.multiselect("Outcome", options=all_outcomes, default=all_outcomes)
        with fcol3:
            metric_choice = st.radio("Metric", ["Avg. Pages", "Avg. Seconds"], horizontal=True)

        fpt = pt[pt["page_type"].isin(selected_pages)]
        fpt = fpt[fpt["revenue_label"].isin(selected_outcomes)]

        c5, c6 = st.columns(2, gap="large")
        if metric_choice == "Avg. Pages":
            with c5:
                st.caption("Average number of pages visited by outcome")
                fig = px.bar(
                    fpt, x="page_type", y="avg_pages", color="revenue_label",
                    barmode="group",
                    labels={"page_type":"Page Type","avg_pages":"Avg. Pages","revenue_label":""},
                    text="avg_pages"
                )
                fig.update_traces(texttemplate="%{text:.2f}")
                st.plotly_chart(fig, use_container_width=True)
        else:
            with c5:
                st.caption("Average time spent (seconds) by outcome")
                fig = px.bar(
                    fpt, x="page_type", y="avg_seconds", color="revenue_label",
                    barmode="group",
                    labels={"page_type":"Page Type","avg_seconds":"Avg. Seconds","revenue_label":""},
                    text="avg_seconds"
                )
                fig.update_traces(texttemplate="%{text:.2f}")
                st.plotly_chart(fig, use_container_width=True)

        with c6:
            st.caption("Data preview & export")
            if st.toggle("Show table", value=False):
                st.dataframe(fpt.sort_values(["page_type","revenue_label"]))
            st.download_button(
                "⬇️ Download (Engagement data)",
                data=fpt.sort_values(["page_type","revenue_label"]).to_csv(index=False).encode("utf-8"),
                file_name="page_type_performance_filtered.csv",
                mime="text/csv",
                use_container_width=True
            )
