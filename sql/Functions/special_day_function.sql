DROP FUNCTION IF EXISTS clickstream.get_special_day_effect(TEXT[], TEXT[], BOOLEAN, INT[], INT[], INT[], INT[], TEXT[]);
CREATE OR REPLACE FUNCTION clickstream.get_special_day_effect(
    p_months TEXT[] DEFAULT NULL, p_visitor_types TEXT[] DEFAULT NULL, p_weekend BOOLEAN DEFAULT NULL,
    p_browsers INT[] DEFAULT NULL, p_os INT[] DEFAULT NULL, p_regions INT[] DEFAULT NULL, p_traffics INT[] DEFAULT NULL, p_page_types TEXT[] DEFAULT NULL
)
RETURNS TABLE (specialday NUMERIC, conversion_rate NUMERIC) AS $$
BEGIN
    RETURN QUERY
    SELECT
        s.specialday::NUMERIC,
        ROUND(100.0 * sum(CASE WHEN s.revenue THEN 1 ELSE 0 END) / NULLIF(count(*), 0), 2)
    FROM clickstream.full_data s
    WHERE (p_months IS NULL OR s.month = ANY(p_months)) AND (p_visitor_types IS NULL OR s.visitortype = ANY(p_visitor_types)) AND
          (p_weekend IS NULL OR s.weekend = p_weekend) AND (p_browsers IS NULL OR s.browser = ANY(p_browsers)) AND
          (p_os IS NULL OR s.operatingsystems = ANY(p_os)) AND (p_regions IS NULL OR s.region = ANY(p_regions)) AND
          (p_traffics IS NULL OR s.traffictype = ANY(p_traffics)) AND
          (p_page_types IS NULL OR (('Administrative' = ANY(p_page_types) AND s.administrative > 0) OR ('Informational' = ANY(p_page_types) AND s.informational > 0) OR ('Product Related' = ANY(p_page_types) AND s.productrelated > 0)))
    GROUP BY s.specialday ORDER BY s.specialday;
END;
$$ LANGUAGE plpgsql;