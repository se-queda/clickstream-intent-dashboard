Clickstream Purchase Intent Dashboard

This project implements an interactive, data‑driven dashboard for analysing
clickstream data and understanding purchase intent. It combines a
PostgreSQL back‑end with a Streamlit front‑end to surface key metrics
about customer behaviour, conversion rates and traffic patterns. The
codebase has been modularised and optimised to make it easy to
maintain, extend and re‑use.

Overview

The underlying dataset is a synthetic clickstream log with
information about user sessions, visitor types, page views and
conversions. The PostgreSQL layer cleans, aggregates and enriches
this data using a series of stored functions and materialised
views. The Streamlit app then calls these functions to display
interactive KPIs, charts and cohort analyses.

Highlights

SQL functions for business logic – All heavy lifting is done
inside PostgreSQL. Functions like get_kpis,
get_weekday_vs_weekend, get_monthwise_revenue and
get_engagement_metrics_impact compute totals, conversion rates
and other aggregated statistics using efficient SQL. This keeps
the Python layer thin and reduces data transfer overhead.

Consolidated full_data view – A denormalised view combines
fact and dimension tables (browser, OS, region, traffic, etc.) so
that filters can be populated without repeatedly joining tables.
This makes the sidebar much more responsive when the user changes
selections.

Cohort analysis views – Additional views such as
monthly_new_vs_returning, weekday_conversion_by_traffic and
browser_os_conversion_matrix provide deeper insights into how
behaviour varies over time, by traffic source or across device
combinations.

Modular Streamlit code – The front‑end has been split into
logical modules:

db_utils.py – wraps the SQLAlchemy connection, loads
dimension names, fetches distinct filter values (falling back
to full_data when available) and executes queries with error
handling. Caching is configured via st.cache_data/cache_resource
to avoid redundant calls.

filters.py – renders the sidebar and constructs a
parameter dictionary based on the selected filter values and
their scope (apply to all charts, KPIs only or a single graph).

charts.py – encapsulates each visualisation in its own
function. Charts include week‑day versus weekend conversion,
month‑wise conversion rate, browser and traffic performance,
region/OS/page type impact, engagement metric comparisons and
special‑day effects. Cohort visualisations are also defined
here.

app.py – orchestrates everything: configures the page,
loads filters, builds parameters, calls the SQL functions and
passes the results to the appropriate chart functions. A
dropdown menu lets users switch between the cohort views and
see the underlying data in a table.

Performance optimisations – By caching dimension lookups and
query results and by querying pre‑aggregated views, the dashboard
remains responsive even on large datasets. The full_data view
eliminates redundant joins for filter lookups. Streamlit’s
caching mechanism is used carefully: unhashable arguments (like
SQLAlchemy engines) are prefixed with underscores to avoid
caching errors, and keys are supplied for Plotly charts to avoid
duplicate element warnings.

Database Setup

Define schema and dimension tables – The sql/ directory
contains scripts for creating the schema (clickstream), base
fact table and dimension tables (dim_browser, dim_os,
dim_region, dim_traffic and others).

Load data – Load your clickstream data into the base fact
table. Scripts in sql/ can be adapted to your data source.

Create functions – SQL files under sql/Functions/ define
functions such as get_kpis, get_weekday_vs_weekend and
get_engagement_metrics_impact. These encapsulate complex
aggregation logic and return a single row or table with the
required metrics.

Create views – Views under sql/views/ expose
pre‑aggregated datasets. full_data.sql flattens the fact and
dimension tables. cohort_views.sql adds the three cohort
analyses used in the dashboard. Materialising these views can
further improve performance.

Execute these scripts in your PostgreSQL instance before running
the Streamlit app.

Running the Dashboard

Clone the repository and install the Python dependencies:

```
git clone https://github.com/se-queda/clickstream-intent-dashboard.git
cd clickstream-intent-dashboard
pip install -r requirements.txt
```

Configure your database credentials in a secrets.toml file
under the project root (Streamlit reads this automatically):

```
[postgres]
user = "your_db_user"
password = "your_db_password"
host = "your_db_host"
port = 5432
dbname = "your_db_name"
```

Launch the dashboard:

```
streamlit run app.py
```

The sidebar lets you filter by month, visitor type, weekend,
browser, operating system, region, traffic source and page type.
You can choose whether a filter applies to all charts, only the
KPIs or just the specific graph it corresponds to. The cohort
analysis section provides a drop‑down to switch between different
cohort views and shows both the chart and the underlying data.

Project Structure

```
clickstream-intent-dashboard/
├── app.py               # Main Streamlit app
├── charts.py            # Plotly visualisation helpers
├── db_utils.py          # Database connection, caching and query helpers
├── filters.py           # Sidebar filters and parameter builder
├── sql/
│   ├── Functions/       # SQL functions for KPIs and charts
│   ├── views/           # SQL views, including full_data and cohorts
│   └── ...              # Schema and data loading scripts
├── requirements.txt     # Python dependencies
└── README.md            # Project documentation (this file)
```

Summary of Enhancements

This refactor took a single monolithic Streamlit script and split it
into well‑defined modules. It also introduced new database
optimisations (such as the full_data view), added cohort analyses,
improved caching and removed duplicate code. The result is a
cleaner, faster, more maintainable dashboard that still provides all
of the original insights – plus a few new ones.
