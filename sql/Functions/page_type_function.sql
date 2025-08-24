DROP FUNCTION IF EXISTS clickstream.get_page_type_performance(TEXT[], TEXT[], BOOLEAN, INT[], INT[], INT[], INT[], TEXT[]);
CREATE OR REPLACE FUNCTION clickstream.get_page_type_performance(
    p_months TEXT[] DEFAULT NULL, p_visitor_types TEXT[] DEFAULT NULL, p_weekend BOOLEAN DEFAULT NULL,
    p_browsers INT[] DEFAULT NULL, p_os INT[] DEFAULT NULL, p_regions INT[] DEFAULT NULL, p_traffics INT[] DEFAULT NULL, p_page_types TEXT[] DEFAULT NULL
)
RETURNS TABLE (page_type TEXT, total_sessions BIGINT, conversion_rate NUMERIC) AS $$
BEGIN
    RETURN QUERY
    SELECT 'Administrative' AS page_type, sum(s.administrative)::BIGINT, ROUND(100.0 * sum(CASE WHEN s.revenue THEN s.administrative ELSE 0 END) / NULLIF(sum(s.administrative), 0), 2)
    FROM clickstream.full_data s
    WHERE (p_months IS NULL OR s.month = ANY(p_months)) AND (p_visitor_types IS NULL OR s.visitortype = ANY(p_visitor_types)) AND (p_weekend IS NULL OR s.weekend = p_weekend) AND (p_browsers IS NULL OR s.browser = ANY(p_browsers)) AND (p_os IS NULL OR s.operatingsystems = ANY(p_os)) AND (p_regions IS NULL OR s.region = ANY(p_regions)) AND (p_traffics IS NULL OR s.traffictype = ANY(p_traffics)) AND (p_page_types IS NULL OR 'Administrative' = ANY(p_page_types))
    UNION ALL
    SELECT 'Informational' AS page_type, sum(s.informational)::BIGINT, ROUND(100.0 * sum(CASE WHEN s.revenue THEN s.informational ELSE 0 END) / NULLIF(sum(s.informational), 0), 2)
    FROM clickstream.full_data s
    WHERE (p_months IS NULL OR s.month = ANY(p_months)) AND (p_visitor_types IS NULL OR s.visitortype = ANY(p_visitor_types)) AND (p_weekend IS NULL OR s.weekend = p_weekend) AND (p_browsers IS NULL OR s.browser = ANY(p_browsers)) AND (p_os IS NULL OR s.operatingsystems = ANY(p_os)) AND (p_regions IS NULL OR s.region = ANY(p_regions)) AND (p_traffics IS NULL OR s.traffictype = ANY(p_traffics)) AND (p_page_types IS NULL OR 'Informational' = ANY(p_page_types))
    UNION ALL
    SELECT 'Product Related' AS page_type, sum(s.productrelated)::BIGINT, ROUND(100.0 * sum(CASE WHEN s.revenue THEN s.productrelated ELSE 0 END) / NULLIF(sum(s.productrelated), 0), 2)
    FROM clickstream.full_data s
    WHERE (p_months IS NULL OR s.month = ANY(p_months)) AND (p_visitor_types IS NULL OR s.visitortype = ANY(p_visitor_types)) AND (p_weekend IS NULL OR s.weekend = p_weekend) AND (p_browsers IS NULL OR s.browser = ANY(p_browsers)) AND (p_os IS NULL OR s.operatingsystems = ANY(p_os)) AND (p_regions IS NULL OR s.region = ANY(p_regions)) AND (p_traffics IS NULL OR s.traffictype = ANY(p_traffics)) AND (p_page_types IS NULL OR 'Product Related' = ANY(p_page_types));
END;
$$ LANGUAGE plpgsql;