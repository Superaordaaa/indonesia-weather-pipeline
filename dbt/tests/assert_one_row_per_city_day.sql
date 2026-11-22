-- Fails if the upsert ever lets a city/day appear twice.
select city, day, count(*) as n
from {{ ref('stg_weather_daily') }}
group by city, day
having count(*) > 1
