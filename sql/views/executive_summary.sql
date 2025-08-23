create or replace view clickstream.executive_summary as
select
    count(*) as total_sessions,
    sum(case when revenue then 1 else 0 end) as total_conversions,
    ROUND(
        100.0 * sum(case when revenue then 1 else 0 end) / count(*),
        2
    ) as overall_conversion_rate
from clickstream.shopper_data;