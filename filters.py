from __future__ import annotations

import streamlit as st
from typing import Dict, Any, Optional


def render_filters(dims: Dict[str, Dict[int, str]], distincts: Dict[str, list]) -> Dict[str, Dict[str, Any]]:
    """Render sidebar filter widgets and return the configuration.

    Parameters
    ----------
    dims : dict
        Mapping of dimension names (browser, os, region, traffic) to
        dictionaries mapping ID to display name.
    distincts : dict
        Mapping of column names to lists of distinct values for filters.

    Returns
    -------
    dict
        ``filter_config`` where each key corresponds to a filter
        (``month``, ``visitor``, ``weekend``, etc.) and maps to a
        dictionary with ``'value'`` and ``'scope'`` entries.
    """
    st.sidebar.title("Filters")
    filter_config: Dict[str, Dict[str, Any]] = {}

    # --- Date & Visitor Filters ---
    with st.sidebar.expander("Date & Visitor Filters", expanded=True):
        filter_config['month'] = {}
        filter_config['month']['value'] = st.multiselect(
            "Month",
            distincts.get("month", []),
        )
        filter_config['month']['scope'] = st.radio(
            "Apply Month to:", ["All", "KPIs", "Graph"], key="month_scope", horizontal=True
        )

        st.markdown("---")
        filter_config['visitor'] = {}
        filter_config['visitor']['value'] = st.multiselect(
            "Visitor Type",
            distincts.get("visitortype", []),
        )
        filter_config['visitor']['scope'] = st.radio(
            "Apply Visitor to:", ["All", "KPIs", "Graph"], key="visitor_scope", horizontal=True
        )

        st.markdown("---")
        weekend_map = {"All": None, "Weekday only": False, "Weekend only": True}
        weekend_choice = st.selectbox("Weekend", list(weekend_map.keys()), index=0)
        filter_config['weekend'] = {'value': weekend_map[weekend_choice]}
        filter_config['weekend']['scope'] = st.radio(
            "Apply Weekend to:", ["All", "KPIs", "Graph"], key="weekend_scope", horizontal=True
        )

    # --- Technical Filters ---
    with st.sidebar.expander("Technical Filters"):
        # Browser filter
        def pretty_multiselect(label, options, id_to_name, key=None):
            return st.multiselect(
                label,
                options,
                format_func=lambda x: id_to_name.get(x, str(x)),
                key=key,
            )

        filter_config['browser'] = {}
        filter_config['browser']['value'] = pretty_multiselect(
            "Browser", distincts.get("browser", []), dims.get("browser", {}), key="browser"
        )
        filter_config['browser']['scope'] = st.radio(
            "Apply Browser to:", ["All", "KPIs", "Graph"], key="browser_scope", horizontal=True
        )
        st.markdown("---")

        # OS filter
        filter_config['os'] = {}
        filter_config['os']['value'] = pretty_multiselect(
            "Operating System", distincts.get("operatingsystems", []), dims.get("os", {}), key="os"
        )
        filter_config['os']['scope'] = st.radio(
            "Apply OS to:", ["All", "KPIs", "Graph"], key="os_scope", horizontal=True
        )

    # --- Source & Content Filters ---
    with st.sidebar.expander("Source & Content Filters"):
        # Region filter
        filter_config['region'] = {}
        filter_config['region']['value'] = pretty_multiselect(
            "Region", distincts.get("region", []), dims.get("region", {}), key="region"
        )
        filter_config['region']['scope'] = st.radio(
            "Apply Region to:", ["All", "KPIs", "Graph"], key="region_scope", horizontal=True
        )
        st.markdown("---")

        # Traffic filter
        filter_config['traffic'] = {}
        filter_config['traffic']['value'] = pretty_multiselect(
            "Traffic Type", distincts.get("traffictype", []), dims.get("traffic", {}), key="traffic"
        )
        filter_config['traffic']['scope'] = st.radio(
            "Apply Traffic to:", ["All", "KPIs", "Graph"], key="traffic_scope", horizontal=True
        )
        st.markdown("---")

        # Page type filter
        filter_config['page_type'] = {}
        filter_config['page_type']['value'] = st.multiselect(
            "Page Type", ["Administrative", "Informational", "Product Related"]
        )
        filter_config['page_type']['scope'] = st.radio(
            "Apply Page Type to:", ["All", "KPIs", "Graph"], key="page_type_scope", horizontal=True
        )

    return filter_config


def build_params(filter_config: Dict[str, Dict[str, Any]], target_graph: Optional[str] = None) -> Dict[str, Any]:
    """Translate filter configuration into query parameter dictionary.

    Parameters
    ----------
    filter_config : dict
        The configuration returned by ``render_filters()``.
    target_graph : str, optional
        Identifier for the graph currently being rendered. Controls the
        scope of filters (e.g. apply some filters only to KPIs or only
        to graphs).

    Returns
    -------
    dict
        Parameter names mapped to selected filter values or ``None``.
    """
    params: Dict[str, Any] = {}
    param_map = {
        'month': 'p_months',
        'visitor': 'p_visitor_types',
        'weekend': 'p_weekend',
        'browser': 'p_browsers',
        'os': 'p_os',
        'region': 'p_regions',
        'traffic': 'p_traffics',
        'page_type': 'p_page_types',
    }

    for name, config in filter_config.items():
        param_name = param_map.get(name)
        if param_name is None:
            continue
        is_active = False
        value = config.get('value')
        # Weekend filter uses None as "All"
        if value or (name == 'weekend' and value is not None):
            scope = config.get('scope', 'All')
            if scope == 'All':
                is_active = True
            elif scope == 'KPIs' and target_graph == 'kpi':
                is_active = True
            elif scope == 'Graph' and target_graph == name:
                is_active = True

        params[param_name] = value if is_active else None
    return params