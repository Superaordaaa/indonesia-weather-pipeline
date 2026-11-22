-- Daily weather with simple, readable categories for dashboards.
select
    city,
    day,
    temperature_min_c,
    temperature_max_c,
    round(temperature_avg_c, 1) as temperature_avg_c,
    precipitation_mm,
    case
        when precipitation_mm = 0   then 'dry'
        when precipitation_mm < 5   then 'light rain'
        when precipitation_mm < 20  then 'moderate rain'
        else 'heavy rain'
    end as rain_category,
    precipitation_mm >= 20 as is_heavy_rain_day,
    wind_speed_max_kmh
from {{ ref('stg_weather_daily') }}
