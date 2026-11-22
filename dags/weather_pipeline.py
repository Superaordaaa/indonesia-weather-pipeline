"""Daily pipeline: Open-Meteo -> raw.weather_daily (Postgres) -> dbt run -> dbt test."""
import os
from datetime import date, datetime, timedelta

from airflow.providers.standard.operators.bash import BashOperator
from airflow.sdk import dag, task

from weather.extract_load import extract_all, load

DBT = "cd /opt/airflow/dbt && dbt {cmd} --project-dir . --profiles-dir ."


@dag(
    dag_id="indonesia_weather_pipeline",
    schedule="@daily",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    default_args={"retries": 2, "retry_delay": timedelta(minutes=2)},
    tags=["demo", "dbt", "postgres"],
)
def weather_pipeline():
    @task
    def extract_and_load() -> int:
        rows = extract_all(today=date.today(), past_days=14)
        return load(rows, os.environ["WAREHOUSE_DSN"])

    dbt_run = BashOperator(task_id="dbt_run", bash_command=DBT.format(cmd="run"))
    dbt_test = BashOperator(task_id="dbt_test", bash_command=DBT.format(cmd="test"))

    extract_and_load() >> dbt_run >> dbt_test


weather_pipeline()
