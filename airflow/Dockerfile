FROM apache/airflow:3.1.3-python3.12

# dbt lives in its own virtualenv so its dependencies never clash with Airflow's.
RUN python -m venv /home/airflow/dbt-venv \
 && /home/airflow/dbt-venv/bin/pip install --no-cache-dir "dbt-postgres~=1.9.0"
ENV PATH="${PATH}:/home/airflow/dbt-venv/bin"
