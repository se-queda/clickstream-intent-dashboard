from __future__ import annotations

import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text


@st.cache_resource
def get_engine():
    """Create a SQLAlchemy engine using credentials from Streamlit secrets.

    Returns
    -------
    sqlalchemy.engine.Engine | None
        A SQLAlchemy engine connected to PostgreSQL or ``None`` if the
        connection could not be established. Errors are surfaced to
        Streamlit via ``st.error``.
    """
    try:
        creds = st.secrets.get("postgres", {})
        user = creds.get("user")
        password = creds.get("password")
        host = creds.get("host")
        port = creds.get("port")
        dbname = creds.get("dbname")
        if not all([user, password, host, port, dbname]):
            raise ValueError("Incomplete database credentials in secrets.toml")
        url = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{dbname}"
        return create_engine(url, pool_pre_ping=True)
    except Exception as e:
        st.error(f"Failed to create database engine. Please check your secrets.toml file. Error: {e}")
        return None


@st.cache_data(ttl=300, show_spinner="Loading dimension labels...")
def load_dims(_engine) -> dict[str, dict[int, str]]:
    """Load friendly names for dimension IDs from the database.

    Parameters
    ----------
    engine : sqlalchemy.engine.Engine | None
        SQLAlchemy engine returned by ``get_engine()``.

    Returns
    -------
    dict[str, dict[int, str]]
        A mapping from dimension name to a dictionary of ID → name.
        If the engine is ``None`` or a query fails, an empty dict is
        returned and an error is displayed via Streamlit.
    """
    if _engine is None:
        return {}
    try:
        with _engine.begin() as con:
            db = pd.read_sql(text("SELECT id, name FROM clickstream.dim_browser ORDER BY id"), con)
            dos = pd.read_sql(text("SELECT id, name FROM clickstream.dim_os ORDER BY id"), con)
            dr = pd.read_sql(text("SELECT id, name FROM clickstream.dim_region ORDER BY id"), con)
            dt = pd.read_sql(text("SELECT id, name FROM clickstream.dim_traffic ORDER BY id"), con)
        return {
            "browser": dict(zip(db["id"], db["name"])),
            "os": dict(zip(dos["id"], dos["name"])),
            "region": dict(zip(dr["id"], dr["name"])),
            "traffic": dict(zip(dt["id"], dt["name"])),
        }
    except Exception as e:
        st.error(f"Failed to load dimension data. Error: {e}")
        return {}


@st.cache_data(ttl=300, show_spinner="Loading filter options...")
def load_distincts(_engine) -> dict[str, object]:
    """
    Load distinct values for sidebar filters.

    In earlier versions of this app, the distinct values for filters were
    obtained directly from the base ``clickstream.shopper_data`` table,
    returning a dictionary of lists. After the introduction of the
    consolidated ``full_data`` view (which denormalises several
    dimensions), many of the filter keys now return a dictionary
    mapping ID values to human–readable names rather than a simple
    list. To accommodate both lists and dictionaries in the return
    value, this function's return type has been broadened to
    ``dict[str, object]`` so type checkers like Pylance do not
    complain when assigning a ``dict`` where a ``list`` was expected.

    Parameters
    ----------
    _engine : sqlalchemy.engine.Engine | None
        SQLAlchemy engine returned by :func:`get_engine`.

    Returns
    -------
    dict[str, object]
        A mapping from filter key to either a list of distinct
        primitive values or a dictionary mapping IDs to human readable
        names. If the engine is ``None`` or an error occurs, an empty
        mapping is returned.
    """
    if _engine is None:
        return {}
    # We intentionally annotate opts with ``dict[str, object]`` to allow
    # storing either lists or dictionaries for different filter keys.
    opts: dict[str, object] = {}
    try:
        with _engine.begin() as con:
            # When using the consolidated ``full_data`` view, certain
            # columns return ID/name pairs. Others simply return a list
            # of distinct values.
            try:
                opts['month'] = pd.read_sql(text("SELECT DISTINCT month FROM clickstream.full_data ORDER BY 1"), con)['month'].tolist()
                opts['visitortype'] = pd.read_sql(text("SELECT DISTINCT visitortype FROM clickstream.full_data ORDER BY 1"), con)['visitortype'].tolist()
                opts['browser'] = pd.read_sql(text("SELECT DISTINCT browser AS id, browser_name AS name FROM clickstream.full_data ORDER BY 1"), con).set_index('id')['name'].to_dict()
                opts['operatingsystems'] = pd.read_sql(text("SELECT DISTINCT operatingsystems AS id, os_name AS name FROM clickstream.full_data ORDER BY 1"), con).set_index('id')['name'].to_dict()
                opts['region'] = pd.read_sql(text("SELECT DISTINCT region AS id, region_name AS name FROM clickstream.full_data ORDER BY 1"), con).set_index('id')['name'].to_dict()
                opts['traffictype'] = pd.read_sql(text("SELECT DISTINCT traffictype AS id, traffic_name AS name FROM clickstream.full_data ORDER BY 1"), con).set_index('id')['name'].to_dict()
            except Exception:
                # Fallback to shopper_data if full_data is not available
                for col in [
                    "month",
                    "visitortype",
                    "weekend",
                    "browser",
                    "operatingsystems",
                    "region",
                    "traffictype",
                ]:
                    q = text(f"SELECT DISTINCT {col} AS v FROM clickstream.shopper_data ORDER BY 1")
                    opts[col] = pd.read_sql(q, con)["v"].tolist()
    except Exception as e:
        st.error(f"Failed to load distinct filter values. Error: {e}")
        return {}
    return opts


def execute_query(engine, query: str, params: dict | None = None) -> pd.DataFrame:
    """Execute a SQL query with optional parameters.

    This wrapper centralises error handling for database operations. It
    returns an empty DataFrame on failure and reports the error to
    Streamlit, ensuring the rest of the app can proceed gracefully.

    Parameters
    ----------
    engine : sqlalchemy.engine.Engine | None
        SQLAlchemy engine returned by ``get_engine()``.
    query : str
        The SQL query to execute. Should be parameterised with
        ``sqlalchemy.text`` for safety.
    params : dict | None
        A dictionary of parameters to bind to the query. Use ``None`` if
        there are no parameters.

    Returns
    -------
    pandas.DataFrame
        A DataFrame containing the query results or empty if an error
        occurred.
    """
    if engine is None:
        return pd.DataFrame()
    try:
        with engine.begin() as con:
            return pd.read_sql(text(query), con, params=params)
    except Exception as e:
        st.error(f"Database query failed. Error: {e}")
        return pd.DataFrame()