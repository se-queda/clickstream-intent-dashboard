import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine, text

st.set_page_config(
    page_title="Clickstream Purchase Intent Dashboard",
    page_icon="🛒",
    layout="wide",
)

# -----------------------------
# DB CONNECTION & SETUP
# -----------------------------
@st.cache_resource
def get_engine():
    """Creates a SQLAlchemy engine from Streamlit secrets."""
    try:
        s = st.secrets["postgres"]
        url = f'postgresql+psycopg2://{s["user"]}:{s["password"]}@{s["host"]}:{s["port"]}/{s["dbname"]}'
        return create_engine(url, pool_pre_ping=True)
    except Exception as e:
        st.error(f"Failed to create database engine. Please check your secrets.toml file. Error: {e}")
        return None

engine = get_engine()

# -----------------------------
# DIMENSION & FILTER VALUE LOADING
# -----------------------------
@st.cache_data(ttl=300, show_spinner="Loading dimension labels...")
def load_dims():
    """Loads friendly names for dimension IDs from the database."""
    if engine is None: return {}
    try:
        with engine.begin() as con:
            db = pd.read_sql(text("SELECT id, name FROM clickstream.dim_browser ORDER BY id"), con)
            dos = pd.read_sql(text("SELECT id, name FROM clickstream.dim_os ORDER BY id"), con)
            dr  = pd.read_sql(text("SELECT id, name FROM clickstream.dim_region ORDER BY id"), con)
            dt  = pd.read_sql(text("SELECT id, name FROM clickstream.dim_traffic ORDER BY id"), con)
        return {
            "browser": dict(zip(db["id"],  db["name"])),
            "os":      dict(zip(dos["id"], dos["name"])),
            "region":  dict(zip(dr["id"],  dr["name"])),
            "traffic": dict(zip(dt["id"],  dt["name"])),
        }
    except Exception as e:
        st.error(f"Failed to load dimension data. Error: {e}")
        return {}

@st.cache_data(show_spinner="Loading filter options...", ttl=300)
def load_distincts():
    """Loads distinct values for sidebar filters from the new full_data view."""
    if engine is None: return {}
    opts = {}
    try:
        with engine.begin() as con:
            # Simplified to query the central view
            opts['month'] = pd.read_sql(text("SELECT DISTINCT month FROM clickstream.full_data ORDER BY 1;"), con)['month'].tolist()
            opts['visitortype'] = pd.read_sql(text("SELECT DISTINCT visitortype FROM clickstream.full_data ORDER BY 1;"), con)['visitortype'].tolist()
            opts['browser'] = pd.read_sql(text("SELECT DISTINCT browser AS id, browser_name AS name FROM clickstream.full_data ORDER BY 1;"), con).set_index('id')['name'].to_dict()
            opts['operatingsystems'] = pd.read_sql(text("SELECT DISTINCT operatingsystems AS id, os_name AS name FROM clickstream.full_data ORDER BY 1;"), con).set_index('id')['name'].to_dict()
            opts['region'] = pd.read_sql(text("SELECT DISTINCT region AS id, region_name AS name FROM clickstream.full_data ORDER BY 1;"), con).set_index('id')['name'].to_dict()
            opts['traffictype'] = pd.read_sql(text("SELECT DISTINCT traffictype AS id, traffic_name AS name FROM clickstream.full_data ORDER BY 1;"), con).set_index('id')['name'].to_dict()
    except Exception as e:
        st.error(f"Failed to load distinct filter values. Error: {e}")
    return opts

# -----------------------------
# SIDEBAR FILTERS
# -----------------------------
st.sidebar.title("Filters")
dims = load_dims()
distincts = load_distincts()

if not dims or not distincts:
    st.sidebar.error("Could not load filter data from the database.")
    st.stop()

def pretty_multiselect(label, options_dict, key=None):
    options = list(options_dict.keys())
    return st.multiselect(
        label,
        options,
        format_func=lambda x: options_dict.get(x, str(x)),
        key=key,
    )

# --- Filter Widgets with Scope Switches ---
filter_config = {}

with st.sidebar.expander("Date & Visitor Filters", expanded=True):
    filter_config['month'] = {'value': st.multiselect("Month", distincts.get("month", []))}
    filter_config['month']['scope'] = st.radio("Apply Month to:", ["All", "KPIs", "Graph"], key="month_scope", horizontal=True)
    st.markdown("---")
    filter_config['visitor'] = {'value': st.multiselect("Visitor Type", distincts.get("visitortype", []))}
    filter_config['visitor']['scope'] = st.radio("Apply Visitor to:", ["All", "KPIs", "Graph"], key="visitor_scope", horizontal=True)
    st.markdown("---")
    weekend_map  = {"All": None, "Weekday only": False, "Weekend only": True}
    weekend_choice = st.selectbox("Weekend", list(weekend_map.keys()), index=0)
    filter_config['weekend'] = {'value': weekend_map[weekend_choice]}
    filter_config['weekend']['scope'] = st.radio("Apply Weekend to:", ["All", "KPIs", "Graph"], key="weekend_scope", horizontal=True)

with st.sidebar.expander("Technical Filters"):
    filter_config['browser'] = {'value': pretty_multiselect("Browser", distincts.get("browser", {}), key="browser")}
    filter_config['browser']['scope'] = st.radio("Apply Browser to:", ["All", "KPIs", "Graph"], key="browser_scope", horizontal=True)
    st.markdown("---")
    filter_config['os'] = {'value': pretty_multiselect("Operating System", distincts.get("operatingsystems", {}), key="os")}
    filter_config['os']['scope'] = st.radio("Apply OS to:", ["All", "KPIs", "Graph"], key="os_scope", horizontal=True)

with st.sidebar.expander("Source & Content Filters"):
    filter_config['region'] = {'value': pretty_multiselect("Region", distincts.get("region", {}), key="region")}
    filter_config['region']['scope'] = st.radio("Apply Region to:", ["All", "KPIs", "Graph"], key="region_scope", horizontal=True)
    st.markdown("---")
    filter_config['traffic'] = {'value': pretty_multiselect("Traffic Type", distincts.get("traffictype", {}), key="traffic")}
    filter_config['traffic']['scope'] = st.radio("Apply Traffic to:", ["All", "KPIs", "Graph"], key="traffic_scope", horizontal=True)
    st.markdown("---")
    filter_config['page_type'] = {'value': st.multiselect("Page Type", ["Administrative", "Informational", "Product Related"])}
    filter_config['page_type']['scope'] = st.radio("Apply Page Type to:", ["All", "KPIs", "Graph"], key="page_type_scope", horizontal=True)

# -----------------------------
# DYNAMIC PARAMETER BUILDER
# -----------------------------
def build_params(target_graph=None):
    params = {}
    param_map = {
        'month': 'p_months', 'visitor': 'p_visitor_types', 'weekend': 'p_weekend',
        'browser': 'p_browsers', 'os': 'p_os', 'region': 'p_regions',
        'traffic': 'p_traffics', 'page_type': 'p_page_types'
    }

    for name, config in filter_config.items():
        param_name = param_map[name]
        is_active = False
        if config['value'] or (name == 'weekend' and config['value'] is not None):
            if config['scope'] == 'All':
                is_active = True
            elif config['scope'] == 'KPIs' and target_graph == 'kpi':
                is_active = True
            elif config['scope'] == 'Graph' and target_graph == name:
                is_active = True
        
        params[param_name] = config['value'] if is_active else None
    return params

# -----------------------------
# DATA LOADING FUNCTION
# -----------------------------
@st.cache_data(show_spinner="Loading data...", ttl=300)
def fetch_query(query, query_params=None):
    try:
        with engine.begin() as con:
            return pd.read_sql(text(query), con, params=query_params)
    except Exception as e:
        st.error(f"Database query failed. Error: {e}")
        return pd.DataFrame()

# -----------------------------
# HEADER + KPIs
# -----------------------------
st.title("🛒 Clickstream Purchase Intent Dashboard")
st.caption("Live from PostgreSQL Functions · filter in the sidebar to slice the insights.")

func_call_str = "SELECT * FROM clickstream.%(func_name)s(:p_months, :p_visitor_types, :p_weekend, :p_browsers, :p_os, :p_regions, :p_traffics, :p_page_types)"

kpi_params = build_params(target_graph='kpi')
kpis = fetch_query(func_call_str % {'func_name': 'get_kpis'}, kpi_params)

total_sessions = int(kpis.iloc[0]['total_sessions']) if not kpis.empty else 0
total_conversions = int(kpis.iloc[0]['total_conversions']) if not kpis.empty else 0
conv_rate = kpis.iloc[0]['overall_conversion_rate'] if not kpis.empty else 0.0

k1, k2, k3 = st.columns(3)
k1.metric("Total Sessions", f"{total_sessions:,}")
k2.metric("Total Conversions", f"{total_conversions:,}")
k3.metric("Overall Conversion Rate", f"{conv_rate or 0:.2f}%")

st.divider()

if total_sessions == 0 and any(p for p in kpi_params.values()):
    st.warning("No data for the current KPI filters. Try widening your selection.")
    # We don't stop here, as graph-specific filters might still yield data

# -----------------------------
# CHARTS (Calling DB Functions)
# -----------------------------
c1, c2 = st.columns(2, gap="large")

with c1:
    st.subheader("Weekday vs Weekend")
    wvw_params = build_params(target_graph='weekend')
    wvw_df = fetch_query(func_call_str % {'func_name': 'get_weekday_vs_weekend'}, wvw_params)
    wvw_df = wvw_df.replace({"weekend": {True: "Weekend", False: "Weekday"}})
    if not wvw_df.empty:
        fig = px.bar(wvw_df, x="weekend", y="conversion_rate", text="conversion_rate", labels={"conversion_rate":"Conversion Rate (%)","weekend":""})
        fig.update_traces(texttemplate="%{text:.2f}%")
        st.plotly_chart(fig, use_container_width=True)

with c2:
    st.subheader("Monthwise Conversion Rate")
    mrev_params = build_params(target_graph='month')
    mrev_df = fetch_query(func_call_str % {'func_name': 'get_monthwise_revenue'}, mrev_params)
    if not mrev_df.empty:
        fig = px.line(mrev_df, x="month", y="conversion_rate", markers=True, labels={"conversion_rate":"Conversion Rate (%)","month":"Month"})
        st.plotly_chart(fig, use_container_width=True)

c3, c4 = st.columns(2, gap="large")

brows_params = build_params(target_graph='browser')
brows_df = fetch_query(func_call_str % {'func_name': 'get_browser_performance'}, brows_params)
with c3:
    st.subheader("Browser Share (by Sessions)")
    if not brows_df.empty:
        fig = px.pie(brows_df, names="name", values="total_sessions", hole=0.45)
        st.plotly_chart(fig, use_container_width=True)
with c4:
    st.subheader("Browser Conversion Rate")
    if not brows_df.empty:
        fig = px.bar(brows_df, x="name", y="conversion_rate", text="conversion_rate", labels={"name":"Browser","conversion_rate":"Conversion Rate (%)"})
        fig.update_traces(texttemplate="%{text:.2f}%")
        st.plotly_chart(fig, use_container_width=True)

c5, c6 = st.columns(2, gap="large")

with c5:
    st.subheader("Traffic Type – Conversion Rate")
    traf_params = build_params(target_graph='traffic')
    traf_df = fetch_query(func_call_str % {'func_name': 'get_traffic_type_performance'}, traf_params)
    if not traf_df.empty:
        fig = px.bar(traf_df, y="name", x="conversion_rate", orientation="h", text="conversion_rate", labels={"name":"Traffic Type","conversion_rate":"Conversion Rate (%)"})
        fig.update_traces(texttemplate="%{text:.2f}%")
        st.plotly_chart(fig, use_container_width=True)

with c6:
    st.subheader("Region – Conversion Rate")
    reg_params = build_params(target_graph='region')
    reg_df = fetch_query(func_call_str % {'func_name': 'get_region_performance'}, reg_params)
    if not reg_df.empty:
        fig = px.bar(reg_df.head(15), x="name", y="conversion_rate", text="conversion_rate", labels={"name":"Region","conversion_rate":"Conversion Rate (%)"})
        fig.update_traces(texttemplate="%{text:.2f}%")
        st.plotly_chart(fig, use_container_width=True)

st.subheader("OS Performance")
os_params = build_params(target_graph='os')
os_df = fetch_query(func_call_str % {'func_name': 'get_os_performance'}, os_params)
if not os_df.empty:
    fig = px.bar(os_df, x="name", y="conversion_rate", text="conversion_rate", labels={"name":"Operating System","conversion_rate":"Conversion Rate (%)"})
    fig.update_traces(texttemplate="%{text:.2f}%")
    st.plotly_chart(fig, use_container_width=True)

st.subheader("Page Type Performance")
page_params = build_params(target_graph='page_type')
page_df = fetch_query(func_call_str % {'func_name': 'get_page_type_performance'}, page_params)
if not page_df.empty:
    fig = px.bar(page_df, x="page_type", y="conversion_rate", text="conversion_rate", labels={"page_type":"Page Type","conversion_rate":"Conversion Rate (%)"})
    fig.update_traces(texttemplate="%{text:.2f}%")
    st.plotly_chart(fig, use_container_width=True)

st.subheader("Engagement Metrics Impact")
eng_params = build_params(target_graph='engagement')
eng_df = fetch_query(func_call_str % {'func_name': 'get_engagement_metrics_impact'}, eng_params)
if not eng_df.empty:
    eng_df_melted = eng_df.melt(id_vars='revenue', var_name='metric', value_name='average_value')
    eng_df_melted['revenue'] = eng_df_melted['revenue'].map({True: 'Converted', False: 'Did Not Convert'})
    
    def format_eng_value(row):
        if row['metric'] in ['avg_bounce_rate', 'avg_exit_rate']:
            return f"{pd.to_numeric(row['average_value'], errors='coerce'):.2%}"
        else:
            return f"${pd.to_numeric(row['average_value'], errors='coerce'):.2f}"
    eng_df_melted['text_value'] = eng_df_melted.apply(format_eng_value, axis=1)

    fig = px.bar(eng_df_melted, x="metric", y="average_value", color="revenue", barmode="group",
                 text='text_value',
                 labels={"metric":"Engagement Metric","average_value":"Average Value", "revenue":"Session Outcome"})
    fig.update_traces(textposition='outside')
    st.plotly_chart(fig, use_container_width=True)

st.subheader("Special Day Effect")
sp_params = build_params(target_graph='special_day')
sp_df = fetch_query(func_call_str % {'func_name': 'get_special_day_effect'}, sp_params)
if not sp_df.empty:
    fig = px.bar(sp_df, x="specialday", y="conversion_rate", text="conversion_rate", labels={"specialday":"Special Day Score","conversion_rate":"Conversion Rate (%)"})
    fig.update_traces(texttemplate="%{text:.2f}%")
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# -----------------------------
# COHORT ANALYSIS SECTION
# -----------------------------
st.header("Cohort Analysis")
cohort_view_choice = st.selectbox(
    "Select a Cohort View",
    ["Monthly New vs. Returning Visitors", "Weekday Conversion by Traffic", "Browser vs. OS Conversion Matrix"]
)

if cohort_view_choice == "Monthly New vs. Returning Visitors":
    st.subheader("Monthly New vs. Returning Visitors")
    df_cohort = fetch_query("SELECT * FROM clickstream.monthly_new_vs_returning;")
    if not df_cohort.empty:
        fig = px.line(df_cohort, x="month", y="conversion_rate", color="visitortype", markers=True,
                      labels={"month": "Month", "conversion_rate": "Conversion Rate (%)", "visitortype": "Visitor Type"})
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(df_cohort, use_container_width=True)

elif cohort_view_choice == "Weekday Conversion by Traffic":
    st.subheader("Weekday Conversion by Traffic")
    df_cohort = fetch_query("SELECT * FROM clickstream.weekday_conversion_by_traffic;")
    if not df_cohort.empty:
        fig = px.bar(df_cohort, x="traffic_name", y="conversion_rate", color="weekend_label", barmode="group",
                     text="conversion_rate",
                     labels={"traffic_name": "Traffic Source", "conversion_rate": "Conversion Rate (%)", "weekend_label": "Day Type"})
        fig.update_traces(texttemplate="%{text:.2f}%")
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(df_cohort, use_container_width=True)

elif cohort_view_choice == "Browser vs. OS Conversion Matrix":
    st.subheader("Browser vs. OS Conversion Matrix")
    df_cohort = fetch_query("SELECT * FROM clickstream.browser_os_conversion_matrix;")
    if not df_cohort.empty:
        # For better visualization, we can pivot the data to create a heatmap
        pivot_df = df_cohort.pivot(index="os_name", columns="browser_name", values="conversion_rate").fillna(0)
        fig = px.imshow(pivot_df, text_auto=".2f", aspect="auto",
                        labels=dict(x="Browser", y="Operating System", color="Conversion Rate (%)"))
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(df_cohort, use_container_width=True)


st.caption("Data source: Logic executed in PostgreSQL Functions and Views.")