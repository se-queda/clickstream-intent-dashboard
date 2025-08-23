DROP VIEW IF EXISTS clickstream.os_performance;

CREATE OR REPLACE VIEW clickstream.os_performance AS
SELECT
    COALESCE(dos.name, CONCAT('OS ', sd.operatingsystems::text)) AS os_name,
    COUNT(*) AS total_sessions,
    SUM(CASE WHEN revenue THEN 1 ELSE 0 END) AS conversions,
    ROUND(SUM(CASE WHEN revenue THEN 1 ELSE 0 END)::NUMERIC / COUNT(*) * 100, 2) AS conversion_rate
FROM clickstream.shopper_data sd
LEFT JOIN clickstream.dim_os dos ON sd.operatingsystems = dos.id
GROUP BY os_name
ORDER BY total_sessions DESC;