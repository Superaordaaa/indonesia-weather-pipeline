-- One row per city over the loaded window: the table a dashboard would read.
select
    city,
    min(day) as first_day,
    max(day) as last_day,
    count(*) as days,
    round(avg(temperature_avg_c), 1) as avg_temperature_c,
    max(temperature_max_c)           as hottest_c,
    sum(precipitation_mm)            as total_rain_mm,
    count(*) filter (where is_heavy_rain_day) as heavy_rain_days
from {{ ref('fct_city_weather_daily') }}
group by city
