CREATE OR REPLACE VIEW clickstream.monthly_new_vs_returning AS
SELECT
    month,
    visitortype,
    count(*) AS total_sessions,
    sum(CASE WHEN revenue THEN 1 ELSE 0 END) AS total_conversions,
    ROUND(100.0 * sum(CASE WHEN revenue THEN 1 ELSE 0 END) / NULLIF(count(*), 0), 2) AS conversion_rate
FROM clickstream.full_data
WHERE visitortype IN ('New_Visitor', 'Returning_Visitor')
GROUP BY month, visitortype
ORDER BY month, visitortype;

CREATE OR REPLACE VIEW clickstream.weekday_conversion_by_traffic AS
SELECT
    weekend_label,
    traffic_name,
    count(*) AS total_sessions,
    sum(CASE WHEN revenue THEN 1 ELSE 0 END) AS total_conversions,
    ROUND(100.0 * sum(CASE WHEN revenue THEN 1 ELSE 0 END) / NULLIF(count(*), 0), 2) AS conversion_rate
FROM clickstream.full_data
GROUP BY weekend_label, traffic_name
ORDER BY weekend_label, conversion_rate DESC;

CREATE OR REPLACE VIEW clickstream.browser_os_conversion_matrix AS
SELECT
    browser_name,
    os_name,
    count(*) AS total_sessions,
    sum(CASE WHEN revenue THEN 1 ELSE 0 END) AS total_conversions,
    ROUND(100.0 * sum(CASE WHEN revenue THEN 1 ELSE 0 END) / NULLIF(count(*), 0), 2) AS conversion_rate
FROM clickstream.full_data
GROUP BY browser_name, os_name
ORDER BY total_sessions DESC;
