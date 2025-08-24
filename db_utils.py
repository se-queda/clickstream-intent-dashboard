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
def load_distincts(_engine) -> dict[str, list]:
    """Load distinct values for sidebar filters from the base data table.

    Parameters
    ----------
    engine : sqlalchemy.engine.Engine | None
        SQLAlchemy engine returned by ``get_engine()``.

    Returns
    -------
    dict[str, list]
        A mapping from column name to the list of distinct values found in
        the ``clickstream.shopper_data`` table. Errors are reported via
        Streamlit and an empty mapping is returned on failure.
    """
    if _engine is None:
        return {}
    opts: dict[str, list] = {}
    try:
        with _engine.begin() as con:
            for col in [
                "month",
                "visitortype",
                "weekend",
                "browser",
                "operatingsystems",
                "region",
                "traffictype",
            ]:
                q = text(f"SELECT DISTINCT {col} AS v FROM clickstream.shopper_data ORDER BY 1;")
                opts[col] = pd.read_sql(q, con)["v"].tolist()
    except Exception as e:
        st.error(f"Failed to load distinct filter values. Error: {e}")
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