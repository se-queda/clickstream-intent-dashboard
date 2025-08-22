CREATE OR REPLACE VIEW clickstream.browser_usage AS
SELECT 
    browser,
    COUNT(*) AS total_sessions,
    SUM(CASE WHEN revenue THEN 1 ELSE 0 END) AS conversions,
    ROUND(SUM(CASE WHEN revenue THEN 1 ELSE 0 END)::NUMERIC / COUNT(*) * 100, 2) AS conversion_rate
FROM clickstream.shopper_data
GROUP BY browser
ORDER BY total_sessions DESC;

