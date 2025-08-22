CREATE OR REPLACE VIEW clickstream.conversion_rates AS
SELECT
    visitortype,
    weekend,
    COUNT(*) AS total_sessions,
    SUM(CASE WHEN revenue THEN 1 ELSE 0 END) AS conversions,
    ROUND(
        100.0 * SUM(CASE WHEN revenue THEN 1 ELSE 0 END) / COUNT(*),
        2
    ) AS conversion_rate
FROM clickstream.shopper_data
GROUP BY visitortype, weekend
ORDER BY conversion_rate DESC;

