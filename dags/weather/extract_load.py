"""Extract daily weather from Open-Meteo (free, no API key) and load it into Postgres.

Kept free of Airflow imports so it can be unit-tested and reused.
"""
from __future__ import annotations

from datetime import date

import requests

API = "https://api.open-meteo.com/v1/forecast"
DAILY_VARS = ["temperature_2m_max", "temperature_2m_min", "precipitation_sum", "wind_speed_10m_max"]

CITIES = {
    "Jakarta": (-6.2088, 106.8456),
    "Surabaya": (-7.2575, 112.7521),
    "Bandung": (-6.9175, 107.6191),
    "Medan": (3.5952, 98.6722),
    "Makassar": (-5.1477, 119.4327),
}

DDL = """
CREATE SCHEMA IF NOT EXISTS raw;
CREATE TABLE IF NOT EXISTS raw.weather_daily (
    city               text    NOT NULL,
    latitude           numeric NOT NULL,
    longitude          numeric NOT NULL,
    day                date    NOT NULL,
    temperature_max_c  numeric,
    temperature_min_c  numeric,
    precipitation_mm   numeric,
    wind_speed_max_kmh numeric,
    loaded_at          timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (city, day)
);
"""

UPSERT = """
INSERT INTO raw.weather_daily (city, latitude, longitude, day, temperature_max_c,
                               temperature_min_c, precipitation_mm, wind_speed_max_kmh)
VALUES (%(city)s, %(latitude)s, %(longitude)s, %(day)s, %(temperature_max_c)s,
        %(temperature_min_c)s, %(precipitation_mm)s, %(wind_speed_max_kmh)s)
ON CONFLICT (city, day) DO UPDATE SET
    temperature_max_c  = EXCLUDED.temperature_max_c,
    temperature_min_c  = EXCLUDED.temperature_min_c,
    precipitation_mm   = EXCLUDED.precipitation_mm,
    wind_speed_max_kmh = EXCLUDED.wind_speed_max_kmh,
    loaded_at          = now();
"""


def fetch_city(city: str, lat: float, lon: float, past_days: int = 14, timeout: int = 30) -> dict:
    r = requests.get(API, params={
        "latitude": lat, "longitude": lon, "daily": ",".join(DAILY_VARS),
        "timezone": "Asia/Jakarta", "past_days": past_days, "forecast_days": 1,
    }, timeout=timeout)
    r.raise_for_status()
    return r.json()


def to_rows(city: str, lat: float, lon: float, payload: dict, today: date) -> list[dict]:
    """Flatten the API's column arrays into rows. Keeps only complete days (before today)."""
    d = payload["daily"]
    rows = []
    for i, day in enumerate(d["time"]):
        if date.fromisoformat(day) >= today:
            continue
        rows.append({
            "city": city, "latitude": lat, "longitude": lon, "day": day,
            "temperature_max_c": d["temperature_2m_max"][i],
            "temperature_min_c": d["temperature_2m_min"][i],
            "precipitation_mm": d["precipitation_sum"][i],
            "wind_speed_max_kmh": d["wind_speed_10m_max"][i],
        })
    return rows


def extract_all(today: date, past_days: int = 14) -> list[dict]:
    rows = []
    for city, (lat, lon) in CITIES.items():
        rows += to_rows(city, lat, lon, fetch_city(city, lat, lon, past_days), today)
    return rows


def load(rows: list[dict], dsn: str) -> int:
    """Idempotent upsert: re-running a day overwrites it instead of duplicating it."""
    import psycopg2  # imported here so tests don't need a database driver

    with psycopg2.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute(DDL)
        if rows:
            cur.executemany(UPSERT, rows)
    return len(rows)
