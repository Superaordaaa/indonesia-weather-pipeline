-- Fails on physically implausible values for Indonesian cities, or min above max.
select *
from {{ ref('stg_weather_daily') }}
where temperature_min_c > temperature_max_c
   or temperature_max_c not between 5 and 45
