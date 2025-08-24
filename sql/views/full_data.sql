CREATE OR REPLACE VIEW clickstream.full_data AS
SELECT
    s.*,
    b.name AS browser_name,
    o.name AS os_name,
    r.name AS region_name,
    t.name AS traffic_name,
    CASE WHEN s.weekend THEN 'Weekend' ELSE 'Weekday' END AS weekend_label
FROM
    clickstream.shopper_data s
LEFT JOIN clickstream.dim_browser b ON s.browser = b.id
LEFT JOIN clickstream.dim_os o ON s.operatingsystems = o.id
LEFT JOIN clickstream.dim_region r ON s.region = r.id
LEFT JOIN clickstream.dim_traffic t ON s.traffictype = t.id;
