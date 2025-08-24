DROP FUNCTION IF EXISTS clickstream.get_traffic_type_performance(TEXT[], TEXT[], BOOLEAN, INT[], INT[], INT[], INT[]);
CREATE OR REPLACE FUNCTION clickstream.get_traffic_type_performance(
    p_months TEXT[] DEFAULT NULL, p_visitor_types TEXT[] DEFAULT NULL, p_weekend BOOLEAN DEFAULT NULL,
    p_browsers INT[] DEFAULT NULL, p_os INT[] DEFAULT NULL, p_regions INT[] DEFAULT NULL, p_traffics INT[] DEFAULT NULL
)
RETURNS TABLE (name TEXT, conversion_rate NUMERIC) AS $$
BEGIN
    RETURN QUERY
    SELECT t.name::TEXT, ROUND(100.0 * sum(CASE WHEN s.revenue THEN 1 ELSE 0 END) / NULLIF(count(s.traffictype), 0), 2)
    FROM clickstream.shopper_data s JOIN clickstream.dim_traffic t ON s.traffictype = t.id
    WHERE (p_months IS NULL OR s.month = ANY(p_months)) AND (p_visitor_types IS NULL OR s.visitortype = ANY(p_visitor_types)) AND
          (p_weekend IS NULL OR s.weekend = p_weekend) AND (p_browsers IS NULL OR s.browser = ANY(p_browsers)) AND
          (p_os IS NULL OR s.operatingsystems = ANY(p_os)) AND (p_regions IS NULL OR s.region = ANY(p_regions)) AND
          (p_traffics IS NULL OR s.traffictype = ANY(p_traffics))
    GROUP BY t.name ORDER BY conversion_rate DESC;
END;
$$ LANGUAGE plpgsql;