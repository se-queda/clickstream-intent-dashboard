DROP VIEW IF EXISTS clickstream.traffic_type_performance;

CREATE OR REPLACE VIEW clickstream.traffic_type_performance AS
SELECT
    COALESCE(dt.name, CONCAT('Traffic ', sd.traffictype::text)) AS traffictype_name,
    COUNT(*) AS total_sessions,
    SUM(CASE WHEN revenue THEN 1 ELSE 0 END) AS conversions,
    ROUND(SUM(CASE WHEN revenue THEN 1 ELSE 0 END)::NUMERIC / COUNT(*) * 100, 2) AS conversion_rate
FROM clickstream.shopper_data sd
LEFT JOIN clickstream.dim_traffic dt ON sd.traffictype = dt.id
GROUP BY traffictype_name
ORDER BY conversions DESC;