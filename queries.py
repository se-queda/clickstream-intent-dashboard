# queries.py
SCHEMA = "clickstream"

VIEWS = {
    "executive": f"{SCHEMA}.executive_summary",
    "wvw": f"{SCHEMA}.weekday_vs_weekend",
    "month": f"{SCHEMA}.monthwise_revenue",
    "conv": f"{SCHEMA}.conversion_rates",
    "spday": f"{SCHEMA}.special_day_effect",
    "browser": f"{SCHEMA}.browser_usage",
    "traffic": f"{SCHEMA}.traffic_type_performance",
    "region": f"{SCHEMA}.region_performance",
    "os": f"{SCHEMA}.os_performance",
    "page_tidy": f"{SCHEMA}.page_type_performance_tidy",
    "page_wide": f"{SCHEMA}.page_type_performance",
}

SQL = {
    "exec": f"SELECT total_sessions, total_conversions, overall_conversion_rate FROM {VIEWS['executive']}",

    "wvw": f"SELECT weekend, total_sessions, conversions, conversion_rate FROM {VIEWS['wvw']} ORDER BY weekend",

    "month": f"SELECT month, total_sessions, conversions, conversion_rate FROM {VIEWS['month']} ORDER BY month",

    "conv": f"SELECT visitortype, weekend, conversion_rate FROM {VIEWS['conv']} ORDER BY visitortype, weekend",

    "spday": f"SELECT specialday, total_sessions, conversions, conversion_rate FROM {VIEWS['spday']} ORDER BY specialday",

    "browser": f"SELECT browser_name, total_sessions, conversions, conversion_rate FROM {VIEWS['browser']} ORDER BY total_sessions DESC",

    "traffic": f"SELECT traffictype_name, total_sessions, conversions, conversion_rate FROM {VIEWS['traffic']} ORDER BY conversion_rate DESC, total_sessions DESC",

    "region": f"SELECT region_name, total_sessions, conversions, conversion_rate FROM {VIEWS['region']} ORDER BY conversions DESC",

    "os": f"SELECT os_name, total_sessions, conversions, conversion_rate FROM {VIEWS['os']} ORDER BY total_sessions DESC",

    "page_tidy": f"SELECT revenue, page_type, avg_pages, avg_seconds FROM {VIEWS['page_tidy']} ORDER BY revenue DESC, page_type",

    "page_wide": f"""
        SELECT revenue,
               avg_admin_pages,    avg_info_pages,    avg_product_pages,
               avg_admin_duration, avg_info_duration, avg_product_duration
        FROM {VIEWS['page_wide']}
        ORDER BY revenue DESC
    """,
}
