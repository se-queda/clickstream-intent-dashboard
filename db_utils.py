from __future__ import annotations

import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text


@st.cache_resource
def get_engine():

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


@st.cache_data(ttl=300, show_spinner="Loading dimension labels…")
def load_dims(_engine) -> dict[str, dict[int, str]]:
    if _engine is None:
        return {}
    try:
        with _engine.begin() as con:
            db  = pd.read_sql(text("SELECT id, name FROM clickstream.dim_browser ORDER BY id"), con)
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

@st.cache_data(ttl=300, show_spinner="Loading filter options…")
def load_distincts(_engine) -> dict[str, list]:
    if _engine is None:
        return {}
    opts: dict[str, list] = {}
    try:
        with _engine.begin() as con:
            for col in ["month", "visitortype", "weekend",
                        "browser", "operatingsystems", "region", "traffictype"]:
                q = text(f"SELECT DISTINCT {col} AS v FROM clickstream.shopper_data ORDER BY 1;")
                opts[col] = pd.read_sql(q, con)["v"].tolist()
    except Exception as e:
        st.error(f"Failed to load distinct filter values. Error: {e}")
    return opts


def execute_query(engine, query: str, params: dict | None = None) -> pd.DataFrame:

    if engine is None:
        return pd.DataFrame()
    try:
        with engine.begin() as con:
            return pd.read_sql(text(query), con, params=params)
    except Exception as e:
        st.error(f"Database query failed. Error: {e}")
        return pd.DataFrame()