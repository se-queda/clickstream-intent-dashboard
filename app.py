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

# -----------------------------
# DIM LABELS (for friendly names)
# -----------------------------
@st.cache_data(ttl=300, show_spinner=False)
def load_dims():
    with get_engine().begin() as con:
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

def pretty_multiselect(label, options, id_to_name, key=None):
    return st.sidebar.multiselect(
        label,
        options,
        format_func=lambda x: id_to_name.get(x, str(x)),
        key=key,
    )

@st.cache_data(show_spinner=False, ttl=300)
def load_distincts():
    with get_engine().begin() as con:
        opts = {}
        for col in ["month", "visitortype", "weekend", "browser", "operatingsystems", "region", "traffictype"]:
            q = text(f"SELECT DISTINCT {col} AS v FROM clickstream.shopper_data ORDER BY 1;")
            opts[col] = pd.read_sql(q, con)["v"].tolist()
    return opts

# -----------------------------
# DATA LOADER (row-level, then aggregate in Python)
# -----------------------------
@st.cache_data(show_spinner=True, ttl=300)
def load_filtered_data(filters):
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

# -----------------------------
# SIDEBAR FILTERS
# -----------------------------
st.sidebar.title("Filters")
dims = load_dims()
distincts = load_distincts()

month_sel    = st.sidebar.multiselect("Month", distincts["month"])
visitor_sel  = st.sidebar.multiselect("Visitor Type", distincts["visitortype"])
weekend_map  = {"All": None, "Weekday only": False, "Weekend only": True}
weekend_choice = st.sidebar.selectbox("Weekend", list(weekend_map.keys()), index=0)

# label-aware selects (show names, return IDs)
browser_sel  = pretty_multiselect("Browser",           distincts["browser"],         dims["browser"], key="browser")
os_sel       = pretty_multiselect("Operating System",  distincts["operatingsystems"], dims["os"],      key="os")
region_sel   = pretty_multiselect("Region",            distincts["region"],          dims["region"],  key="region")
traffic_sel  = pretty_multiselect("Traffic Type",      distincts["traffictype"],     dims["traffic"], key="traffic")

filters = {
    "month": month_sel,
    "visitortype": visitor_sel,
    "browser": browser_sel,
    "operatingsystems": os_sel,
    "region": region_sel,
    "traffictype": traffic_sel,
    "weekend": weekend_map[weekend_choice],
}

df, debug = load_filtered_data(filters)

# -----------------------------
# HEADER + KPIs
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

# SQL Debug expander
with st.expander("🛠 SQL Debug"):
    st.write("**WHERE clause**")
    st.code(debug["where_sql"], language="sql")
    st.write("**Parameters**")
    st.json(debug["params"])
    st.write("**Full query**")
    st.code(debug["query"], language="sql")

st.divider()

# If no rows after filters
if df.empty:
    st.warning("No data for the current filters. Try widening your selection.")
    st.stop()

# Add friendly label columns (keep IDs for filtering)
df["browser_label"] = df["browser"].map(dims["browser"]).fillna(df["browser"].astype(str))
df["os_label"]      = df["operatingsystems"].map(dims["os"]).fillna(df["operatingsystems"].astype(str))
df["region_label"]  = df["region"].map(dims["region"]).fillna(df["region"].astype(str))
df["traffic_label"] = df["traffictype"].map(dims["traffic"]).fillna(df["traffictype"].astype(str))

# -----------------------------
# CHARTS
# -----------------------------
# 1) Weekday vs Weekend
c1, c2 = st.columns(2, gap="large")

wvw = (df.groupby("weekend", dropna=False)["revenue"]
         .agg(total_sessions="count", conversions="sum"))
wvw["conversion_rate"] = (wvw["conversions"] / wvw["total_sessions"] * 100).round(2)
wvw = wvw.reset_index().replace({"weekend": {True: "Weekend", False: "Weekday"}})

with c1:
    st.subheader("Weekday vs Weekend")
    fig = px.bar(wvw, x="weekend", y="conversion_rate",
                 text="conversion_rate", labels={"conversion_rate":"Conversion Rate (%)","weekend":""})
    fig.update_traces(texttemplate="%{text:.2f}%")
    st.plotly_chart(fig, use_container_width=True)

# 2) Monthwise Conversion Rate
mrev = (df.groupby("month", dropna=False)["revenue"]
          .agg(total_sessions="count", conversions="sum"))
mrev["conversion_rate"] = (mrev["conversions"] / mrev["total_sessions"] * 100).round(2)
mrev = mrev.reset_index().sort_values("month")

with c2:
    st.subheader("Monthwise Conversion Rate")
    fig = px.line(mrev, x="month", y="conversion_rate", markers=True,
                  labels={"conversion_rate":"Conversion Rate (%)","month":"Month"})
    st.plotly_chart(fig, use_container_width=True)

# 3) Browser Usage
c3, c4 = st.columns(2, gap="large")
brows = (df.groupby("browser_label", dropna=False)["revenue"]
           .agg(total_sessions="count", conversions="sum")
           .reset_index()
           .sort_values("total_sessions", ascending=False))
brows["conversion_rate"] = (brows["conversions"] / brows["total_sessions"] * 100).round(2)

with c3:
    st.subheader("Browser Share (by Sessions)")
    fig = px.pie(brows, names="browser_label", values="total_sessions", hole=0.45)
    st.plotly_chart(fig, use_container_width=True)

with c4:
    st.subheader("Browser Conversion Rate")
    fig = px.bar(brows, x="browser_label", y="conversion_rate",
                 labels={"browser_label":"Browser","conversion_rate":"Conversion Rate (%)"},
                 text="conversion_rate")
    fig.update_traces(texttemplate="%{text:.2f}%")
    st.plotly_chart(fig, use_container_width=True)

# 4) Traffic Type Performance
c5, c6 = st.columns(2, gap="large")
traf = (df.groupby("traffic_label", dropna=False)["revenue"]
          .agg(total_sessions="count", conversions="sum")
          .reset_index())
traf["conversion_rate"] = (traf["conversions"] / traf["total_sessions"] * 100).round(2)
traf = traf.sort_values(["conversion_rate", "total_sessions"], ascending=[False, False])

with c5:
    st.subheader("Traffic Type – Conversion Rate")
    fig = px.bar(traf, y="traffic_label", x="conversion_rate", orientation="h",
                 labels={"traffic_label":"Traffic Type","conversion_rate":"Conversion Rate (%)"},
                 text="conversion_rate")
    fig.update_traces(texttemplate="%{text:.2f}%")
    st.plotly_chart(fig, use_container_width=True)

# 5) Region Performance
reg = (df.groupby("region_label", dropna=False)["revenue"]
         .agg(total_sessions="count", conversions="sum")
         .reset_index()
         .sort_values("conversions", ascending=False))
reg["conversion_rate"] = (reg["conversions"] / reg["total_sessions"] * 100).round(2)

with c6:
    st.subheader("Region – Conversions & Rate")
    fig = px.bar(reg.head(15), x="region_label", y="conversions",
                 labels={"region_label":"Region","conversions":"Conversions"})
    st.plotly_chart(fig, use_container_width=True)

# 6) Special Day Effect
st.subheader("Special Day Effect")
sp = (df.groupby("specialday", dropna=False)["revenue"]
        .agg(total_sessions="count", conversions="sum"))
sp["conversion_rate"] = (sp["conversions"] / sp["total_sessions"] * 100).round(2)
sp = sp.reset_index().sort_values("specialday")

fig = px.bar(sp, x="specialday", y="conversion_rate",
             labels={"specialday":"Special Day Score","conversion_rate":"Conversion Rate (%)"},
             text="conversion_rate")
fig.update_traces(texttemplate="%{text:.2f}%")
st.plotly_chart(fig, use_container_width=True)

st.caption("Data source: clickstream.shopper_data • Charts update with sidebar filters.")
