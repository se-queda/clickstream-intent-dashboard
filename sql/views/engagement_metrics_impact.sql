CREATE OR REPLACE VIEW clickstream.engagement_metrics_impact AS
SELECT
    revenue,
    AVG(bouncerates) AS avg_bounce_rate,
    AVG(exitrates) AS avg_exit_rate,
    AVG(pagevalues) AS avg_page_value
FROM clickstream.shopper_data
GROUP BY revenue;