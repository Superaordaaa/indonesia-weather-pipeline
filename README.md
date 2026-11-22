# indonesia-weather-pipeline

[![tests](https://github.com/Superaordaaa/indonesia-weather-pipeline/actions/workflows/tests.yml/badge.svg)](https://github.com/Superaordaaa/indonesia-weather-pipeline/actions/workflows/tests.yml)

A small end-to-end data platform you can run on a laptop with one command. **Apache Airflow 3** pulls daily weather for five Indonesian cities from a public API, loads it into **PostgreSQL**, transforms it with **dbt**, and checks it with dbt tests.

It's a public, simplified version of the stack I work with day to day (Airflow + dbt + Postgres), built so anyone can clone it and see every layer.

```
Open-Meteo API (free, no key)
      │  Airflow task: extract_and_load  (Python, idempotent upsert)
      ▼
PostgreSQL  raw.weather_daily              one row per city per day
      │  Airflow task: dbt_run
      ▼
staging.stg_weather_daily   (view)          typed and cleaned
marts.fct_city_weather_daily (table)        + rain categories
marts.city_weather_summary   (table)        one row per city, ready for a dashboard
      │  Airflow task: dbt_test
      ▼
8 data tests: not_null, unique, accepted_values, one row per city/day, sane temperatures
```

## Run it
Requires Docker Desktop.
```bash
docker compose up -d --build
```
- Airflow UI: http://localhost:8080 (local demo, no login). Trigger `indonesia_weather_pipeline`.
- Or run the whole DAG from the terminal:
  ```bash
  docker compose exec airflow airflow dags test indonesia_weather_pipeline
  ```
- Query the warehouse at `localhost:5433` (user and password `warehouse`):
  ```bash
  docker compose exec postgres psql -U warehouse -d warehouse -c "select * from marts.city_weather_summary"
  ```

Example output from a real run (14 days ending 21 Nov 2026):
```
   city   | days | avg_temperature_c | hottest_c | total_rain_mm | heavy_rain_days
----------+------+-------------------+-----------+---------------+-----------------
 Medan    |   14 |              27.1 |      31.8 |         382.7 |              10
 Bandung  |   14 |              26.1 |      33.9 |          89.0 |               0
 Jakarta  |   14 |              29.7 |      35.0 |          87.6 |               0
 Makassar |   14 |              28.8 |      33.1 |          81.3 |               0
 Surabaya |   14 |              30.5 |      36.0 |          68.2 |               0
```

Stop with `docker compose down`. Add `-v` to also delete the data.

## Design decisions
- **Idempotent loads.** Each run re-fetches the last 14 days and upserts on `(city, day)`. Re-running or backfilling never creates duplicates, and a dbt test enforces this.
- **Only complete days.** Today's partial values are skipped, so a day is loaded once its data is final.
- **dbt in its own virtualenv** inside the Airflow image, so dbt and Airflow dependencies never conflict.
- **Extract logic has no Airflow imports** (`dags/weather/extract_load.py`), so it can be unit-tested without Airflow, a database, or network access.
- **One Postgres server, two databases:** Airflow metadata (`airflow`) and the warehouse (`warehouse`).

## Project layout
```
dags/weather_pipeline.py        DAG: extract_and_load >> dbt_run >> dbt_test
dags/weather/extract_load.py    API client, row flattening, upsert
dbt/models/staging/             source + staging view
dbt/models/marts/               fact table + summary
dbt/tests/                      custom data tests
airflow/Dockerfile              Airflow 3.1 + dbt-postgres venv
postgres/init.sql               creates the two databases
tests/                          Python unit tests (offline)
```

## Tests
```bash
python -m unittest discover -s tests -v      # Python, offline
docker compose exec airflow bash -c "cd /opt/airflow/dbt && dbt test"   # data tests
```

## Roadmap
- Add failure alerts with [airflow-llm-alerting](https://github.com/Superaordaaa/airflow-llm-alerting)
- Add ClickHouse as the serving layer for the marts
- Deploy to a cloud provider (managed Postgres, object storage for raw files)

Weather data: [Open-Meteo](https://open-meteo.com), CC BY 4.0.

## License
MIT
