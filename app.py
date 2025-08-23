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
# DB CONNECTION
# -----------------------------
def get_engine():
    s = st.secrets["postgres"]
    url = f'postgresql+psycopg2://{s["user"]}:{s["password"]}@{s["host"]}:{s["port"]}/{s["dbname"]}'
    return create_engine(url, pool_pre_ping=True)

# --- Pull small dimension tables for labels ---
@st.cache_data(ttl=300, show_spinner=False)
def load_dims():
    with get_engine().begin() as con:
        db = pd.read_sql(text("SELECT id, name FROM clickstream.dim_browser ORDER BY id"), con)
        dos = pd.read_sql(text("SELECT id, name FROM clickstream.dim_os ORDER BY id"), con)
        dr  = pd.read_sql(text("SELECT id, name FROM clickstream.dim_region ORDER BY id"), con)
        dt  = pd.read_sql(text("SELECT id, name FROM clickstream.dim_traffic ORDER BY id"), con)
    # Make dicts id->name for mapping
    return {
        "browser": dict(zip(db["id"], db["name"])),
        "os":      dict(zip(dos["id"], dos["name"])),
        "region":  dict(zip(dr["id"],  dr["name"])),
        "traffic": dict(zip(dt["id"],  dt["name"])),
    }

def pretty_multiselect(label, options, id_to_name, key=None):
    # options are numeric IDs; show names but return IDs
    return st.sidebar.multiselect(
        label,
        options,
        format_func=lambda x: id_to_name.get(x, str(x)),
        key=key,
        placeholder="All"
    )

@st.cache_data(show_spinner=False, ttl=300)
def load_distincts():
    with get_engine().begin() as con:
        opts = {}
        for col in ["month", "visitortype", "weekend", "browser", "operatingsystems", "region", "traffictype"]:
            q = text(f"SELECT DISTINCT {col} AS v FROM clickstream.shopper_data ORDER BY 1;")
            opts[col] = pd.read_sql(q, con)["v"].tolist()
    return opts

@st.cache_data(show_spinner=True, ttl=300)
def load_filtered_data(filters):
    """Return filtered dataframe + a small debug bundle (query, where, params)."""
    where = []
    params = {}

    def add_list_filter(col, values):
        if values:
            where.append(f"{col} = ANY(:{col})")
            params[col] = values

    def add_bool_filter(col, valmap):
        if valmap is not None:
            where.append(f"{col} = :{col}")
            params[col] = valmap

    add_list_filter("month", filters["month"])
    add_list_filter("visitortype", filters["visitortype"])
    add_list_filter("browser", filters["browser"])
    add_list_filter("operatingsystems", filters["operatingsystems"])
    add_list_filter("region", filters["region"])
    add_list_filter("traffictype", filters["traffictype"])
    add_bool_filter("weekend", filters["weekend"])

    where_sql = ("WHERE " + " AND ".join(where)) if where else ""
    query = f"""
        SELECT
          administrative, administrative_duration,
          informational, informational_duration,
          productrelated, productrelated_duration,
          bouncerates, exitrates, pagevalues,
          specialday, month,
          operatingsystems, browser, region, traffictype,
          visitortype, weekend, revenue
        FROM clickstream.shopper_data
        {where_sql}
    """
    sql = text(query)

    with get_engine().begin() as con:
        df = pd.read_sql(sql, con, params=params)

    debug = {
        "where_sql": where_sql or "-- no WHERE filters applied --",
        "params": params,
        "query": query.strip()
    }
    return df, debug

def download_button(df: pd.DataFrame, label: str, filename: str):
    st.download_button(
        label=label,
        data=df.to_csv(index=False).encode("utf-8"),
        file_name=filename,
        mime="text/csv",
        use_container_width=True
    )

# -----------------------------
# SIDEBAR FILTERS
# -----------------------------
st.sidebar.title("Filters")

# Reset filters button
if st.sidebar.button("🔄 Reset filters"):
    for k in list(st.session_state.keys()):
        if k in ("browser", "os", "region", "traffic"):
            st.session_state[k] = []
    st.rerun()

dims = load_dims()          # id->name maps
distincts = load_distincts()

month_sel    = st.sidebar.multiselect("Month", distincts["month"], placeholder="All")
visitor_sel  = st.sidebar.multiselect("Visitor Type", distincts["visitortype"], placeholder="All")
weekend_map  = {"All": None, "Weekday only": False, "Weekend only": True}
weekend_choice = st.sidebar.selectbox("Weekend", list(weekend_map.keys()), index=0)

# label-aware multiselects (show names, return IDs)
browser_sel  = pretty_multiselect("Browser",          distincts["browser"],         dims["browser"], key="browser")
os_sel       = pretty_multiselect("Operating System", distincts["operatingsystems"], dims["os"],      key="os")
region_sel   = pretty_multiselect("Region",           distincts["region"],          dims["region"],  key="region")
traffic_sel  = pretty_multiselect("Traffic Type",     distincts["traffictype"],     dims["traffic"], key="traffic")

filters = {
    "month": month_sel,
    "visitortype": visitor_sel,
    "browser": browser_sel,                 # still IDs
    "operatingsystems": os_sel,             # IDs
    "region": region_sel,                   # IDs
    "traffictype": traffic_sel,             # IDs
    "weekend": weekend_map[weekend_choice],
}

df, debug = load_filtered_data(filters)


# Add friendly label columns for plotting (keep IDs in df for filtering)
if not df.empty:
    df["browser_label"] = df["browser"].map(dims["browser"]).fillna(df["browser"].astype(str))
    df["os_label"]      = df["operatingsystems"].map(dims["os"]).fillna(df["operatingsystems"].astype(str))
    df["region_label"]  = df["region"].map(dims["region"]).fillna(df["region"].astype(str))
    df["traffic_label"] = df["traffictype"].map(dims["traffic"]).fillna(df["traffictype"].astype(str))

# -----------------------------
# KPI ROW (Executive Summary)
# -----------------------------
st.title("🛒 Clickstream Purchase Intent Dashboard")
st.caption("Live from PostgreSQL · filter in the sidebar to slice the insights.")

total_sessions = len(df)
total_conversions = int(df["revenue"].sum()) if not df.empty else 0
conv_rate = (total_conversions / total_sessions * 100) if total_sessions else 0

k1, k2, k3 = st.columns(3)
k1.metric("Total Sessions", f"{total_sessions:,}")
k2.metric("Total Conversions", f"{total_conversions:,}")
k3.metric("Overall Conversion Rate", f"{conv_rate:.2f}%")

st.divider()
with st.expander("🛠 SQL Debug"):
    st.write("**WHERE clause**")
    st.code(debug["where_sql"], language="sql")
    st.write("**Parameters**")
    st.json(debug["params"])
    st.write("**Full query**")
    st.code(debug["query"], language="sql")
# -----------------------------
# Tabs + Charts
# -----------------------------
if df.empty:
    st.warning("No data for the current filters. Try widening your selection.")
    st.stop()

tab_overview, tab_channels, tab_engagement, tab_geo = st.tabs(
    ["Overview", "Channels", "Engagement", "Geography"]
)

# ============= Overview =============
with tab_overview:
    c1, c2 = st.columns(2, gap="large")

    # Weekday vs Weekend
    wvw = (df.groupby("weekend", dropna=False)["revenue"]
             .agg(total_sessions="count", conversions="sum"))
    wvw["conversion_rate"] = (wvw["conversions"] / wvw["total_sessions"] * 100).round(2)
    wvw = wvw.reset_index().replace({"weekend": {True: "Weekend", False: "Weekday"}})

    with c1:
        st.subheader("Weekday vs Weekend")
        fig = px.bar(
            wvw, x="weekend", y="conversion_rate",
            text="conversion_rate",
            labels={"conversion_rate":"Conversion Rate (%)","weekend":""}
        )
        fig.update_traces(texttemplate="%{text:.2f}%")
        st.plotly_chart(fig, use_container_width=True)
        download_button(wvw, "⬇️ Download (Weekday vs Weekend)", "weekday_vs_weekend.csv")

    # Monthwise trend
    mrev = (df.groupby("month", dropna=False)["revenue"]
              .agg(total_sessions="count", conversions="sum"))
    mrev["conversion_rate"] = (mrev["conversions"] / mrev["total_sessions"] * 100).round(2)
    mrev = mrev.reset_index().sort_values("month")

    with c2:
        st.subheader("Monthwise Conversion Rate")
        fig = px.line(
            mrev, x="month", y="conversion_rate", markers=True,
            labels={"conversion_rate":"Conversion Rate (%)","month":"Month"}
        )
        st.plotly_chart(fig, use_container_width=True)
        download_button(mrev, "⬇️ Download (Monthwise)", "monthwise_conversion.csv")

    # Visitor Type × Weekend
    st.subheader("Visitor Type × Weekend")
    vtw = (df.groupby(["visitortype","weekend"], dropna=False)["revenue"]
             .agg(total_sessions="count", conversions="sum").reset_index())
    vtw["conversion_rate"] = (vtw["conversions"] / vtw["total_sessions"] * 100).round(2)
    vtw["weekend_label"] = vtw["weekend"].map({True:"Weekend", False:"Weekday"})
    fig = px.bar(
        vtw, x="visitortype", y="conversion_rate", color="weekend_label",
        barmode="group",
        labels={"visitortype":"Visitor Type","conversion_rate":"Conversion Rate (%)","weekend_label":""},
        text="conversion_rate"
    )
    fig.update_traces(texttemplate="%{text:.2f}%")
    st.plotly_chart(fig, use_container_width=True)
    download_button(vtw, "⬇️ Download (VisitorType × Weekend)", "visitor_weekend.csv")


# ============= Channels (Browser / Traffic) =============
with tab_channels:
    c3, c4 = st.columns(2, gap="large")

    # Browser Usage
    brows = (df.groupby("browser_label", dropna=False)["revenue"]
               .agg(total_sessions="count", conversions="sum").reset_index())
    brows["conversion_rate"] = (brows["conversions"] / brows["total_sessions"] * 100).round(2)
    brows = brows.sort_values("total_sessions", ascending=False)

    with c3:
        st.subheader("Browser Share (by Sessions)")
        fig = px.pie(brows, names="browser_label", values="total_sessions", hole=0.45)
        st.plotly_chart(fig, use_container_width=True)

        fig = px.bar(
            brows, x="browser_label", y="conversion_rate",
            labels={"browser_label":"Browser","conversion_rate":"Conversion Rate (%)"},
            text="conversion_rate"
        )
        fig.update_traces(texttemplate="%{text:.2f}%")
        st.plotly_chart(fig, use_container_width=True)
        download_button(brows, "⬇️ Download (Browser)", "browser_metrics.csv")

    # Traffic Type Performance
    traf = (df.groupby("traffic_label", dropna=False)["revenue"]
              .agg(total_sessions="count", conversions="sum").reset_index())
    traf["conversion_rate"] = (traf["conversions"] / traf["total_sessions"] * 100).round(2)
    traf = traf.sort_values(["conversion_rate", "total_sessions"], ascending=[False, False])

    with c4:
        st.subheader("Traffic Type – Conversion Rate")
        fig = px.bar(
            traf, y="traffic_label", x="conversion_rate", orientation="h",
            labels={"traffic_label":"Traffic Type","conversion_rate":"Conversion Rate (%)"},
            text="conversion_rate"
        )
        fig.update_traces(texttemplate="%{text:.2f}%")
        st.plotly_chart(fig, use_container_width=True)
        download_button(traf, "⬇️ Download (Traffic Type)", "traffic_metrics.csv")


# ============= Engagement (Page types) =============
with tab_engagement:
    st.subheader("Page Type Performance (Avg pages & time by purchase outcome)")
    # compute per-outcome averages
    cols_pages = ["administrative","informational","productrelated"]
    cols_dur   = ["administrative_duration","informational_duration","productrelated_duration"]

    pt_pages = df.groupby("revenue", dropna=False)[cols_pages].mean().round(2).reset_index()
    pt_dur   = df.groupby("revenue", dropna=False)[cols_dur].mean().round(2).reset_index()

    # reshape for tidy plotting
    pages_m = pt_pages.melt(id_vars="revenue", var_name="page_type", value_name="avg_pages")
    dur_m   = pt_dur.melt(id_vars="revenue", var_name="page_type", value_name="avg_seconds")
    pages_m["revenue_label"] = pages_m["revenue"].map({True:"Purchased", False:"No Purchase"})
    dur_m["revenue_label"]   = dur_m["revenue"].map({True:"Purchased", False:"No Purchase"})

    c5, c6 = st.columns(2, gap="large")

    with c5:
        st.caption("Average number of pages visited by outcome")
        fig = px.bar(
            pages_m, x="page_type", y="avg_pages", color="revenue_label", barmode="group",
            labels={"page_type":"Page Type","avg_pages":"Avg. Pages","revenue_label":""},
            text="avg_pages"
        )
        st.plotly_chart(fig, use_container_width=True)
        download_button(pt_pages, "⬇️ Download (Page Counts by Outcome)", "page_counts_outcome.csv")

    with c6:
        st.caption("Average time spent (seconds) by outcome")
        fig = px.bar(
            dur_m, x="page_type", y="avg_seconds", color="revenue_label", barmode="group",
            labels={"page_type":"Page Type","avg_seconds":"Avg. Seconds","revenue_label":""},
            text="avg_seconds"
        )
        st.plotly_chart(fig, use_container_width=True)
        download_button(pt_dur, "⬇️ Download (Page Durations by Outcome)", "page_durations_outcome.csv")


# ============= Geography =============
with tab_geo:
    st.subheader("Region – Conversions & Conversion Rate")
    reg = (df.groupby("region_label", dropna=False)["revenue"]
             .agg(total_sessions="count", conversions="sum").reset_index())
    reg["conversion_rate"] = (reg["conversions"] / reg["total_sessions"] * 100).round(2)
    reg = reg.sort_values("conversions", ascending=False)

    c7, c8 = st.columns(2, gap="large")
    with c7:
        fig = px.bar(reg.head(15), x="region_label", y="conversions",
                     labels={"region_label":"Region","conversions":"Conversions"})
        st.plotly_chart(fig, use_container_width=True)

    with c8:
        fig = px.bar(reg.head(15), x="region_label", y="conversion_rate",
                     labels={"region_label":"Region","conversion_rate":"Conversion Rate (%)"},
                     text="conversion_rate")
        fig.update_traces(texttemplate="%{text:.2f}%")
        st.plotly_chart(fig, use_container_width=True)

    download_button(reg, "⬇️ Download (Region)", "region_metrics.csv")

st.caption("Data source: clickstream.shopper_data • Charts update with sidebar filters.")
