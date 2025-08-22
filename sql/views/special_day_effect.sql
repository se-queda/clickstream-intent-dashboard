CREATE OR REPLACE VIEW clickstream.special_day_effect AS
SELECT
    specialday,
    COUNT(*) AS total_sessions,
    SUM(CASE WHEN revenue THEN 1 ELSE 0 END) AS conversions,
    ROUND(SUM(CASE WHEN revenue THEN 1 ELSE 0 END)::NUMERIC / NULLIF(COUNT(*), 0) * 100, 2) AS conversion_rate
FROM clickstream.shopper_data
GROUP BY specialday
ORDER BY specialday;