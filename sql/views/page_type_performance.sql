CREATE OR REPLACE VIEW clickstream.page_type_performance AS
SELECT
    revenue,
    AVG(administrative) AS avg_admin_pages,
    AVG(administrative_duration) AS avg_admin_duration,
    AVG(informational) AS avg_info_pages,
    AVG(informational_duration) AS avg_info_duration,
    AVG(productrelated) AS avg_product_pages,
    AVG(productrelated_duration) AS avg_product_duration
FROM clickstream.shopper_data
GROUP BY revenue;
