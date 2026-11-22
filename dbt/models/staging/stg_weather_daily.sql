-- One clean row per city per day.
select
    city,
    day,
    temperature_max_c::numeric(5, 1)  as temperature_max_c,
    temperature_min_c::numeric(5, 1)  as temperature_min_c,
    (temperature_max_c + temperature_min_c) / 2.0 as temperature_avg_c,
    coalesce(precipitation_mm, 0)::numeric(6, 1) as precipitation_mm,
    wind_speed_max_kmh::numeric(5, 1) as wind_speed_max_kmh,
    loaded_at
from {{ source('raw', 'weather_daily') }}
