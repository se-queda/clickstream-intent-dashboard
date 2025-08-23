DROP VIEW IF EXISTS clickstream.browser_usage;

CREATE VIEW clickstream.browser_usage AS
SELECT 
    COALESCE(db.name, CONCAT('Browser ', sd.browser::text)) AS browser_name,
    COUNT(*) AS total_sessions,
    SUM(CASE WHEN revenue THEN 1 ELSE 0 END) AS conversions,
    ROUND(SUM(CASE WHEN revenue THEN 1 ELSE 0 END)::NUMERIC / COUNT(*) * 100, 2) AS conversion_rate
FROM clickstream.shopper_data sd
LEFT JOIN clickstream.dim_browser db ON sd.browser = db.id
GROUP BY browser_name
ORDER BY total_sessions DESC;
