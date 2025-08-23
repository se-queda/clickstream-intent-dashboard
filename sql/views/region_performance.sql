DROP VIEW IF EXISTS clickstream.region_performance;

CREATE OR REPLACE VIEW clickstream.region_performance AS
SELECT
    COALESCE(dr.name, CONCAT('Region ', sd.region::text)) AS region_name,
    COUNT(*) AS total_sessions,
    SUM(CASE WHEN revenue THEN 1 ELSE 0 END) AS conversions,
    ROUND(SUM(CASE WHEN revenue THEN 1 ELSE 0 END)::NUMERIC / COUNT(*) * 100, 2) AS conversion_rate
FROM clickstream.shopper_data sd
LEFT JOIN clickstream.dim_region dr ON sd.region = dr.id
GROUP BY region_name
ORDER BY conversions DESC;
