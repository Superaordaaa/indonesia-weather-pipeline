"""Unit tests for the extract step. No Airflow, database, or network needed."""
import sys
import unittest
from datetime import date
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "dags"))
from weather import extract_load as el  # noqa: E402

PAYLOAD = {"daily": {
    "time": ["2026-11-20", "2026-11-21", "2026-11-22"],
    "temperature_2m_max": [33.1, 32.4, 31.0],
    "temperature_2m_min": [25.0, 24.8, 25.2],
    "precipitation_sum": [0.0, 12.5, None],
    "wind_speed_10m_max": [14.2, 18.9, 10.0],
}}


class TestToRows(unittest.TestCase):
    def test_flattens_arrays_and_drops_incomplete_today(self):
        rows = el.to_rows("Jakarta", -6.2, 106.8, PAYLOAD, today=date(2026, 11, 22))
        self.assertEqual([r["day"] for r in rows], ["2026-11-20", "2026-11-21"])
        self.assertEqual(rows[1]["precipitation_mm"], 12.5)
        self.assertEqual(rows[0]["city"], "Jakarta")

    def test_rows_match_upsert_placeholders(self):
        row = el.to_rows("Jakarta", -6.2, 106.8, PAYLOAD, today=date(2026, 11, 22))[0]
        for key in row:
            self.assertIn(f"%({key})s", el.UPSERT)


class TestExtractAll(unittest.TestCase):
    @mock.patch.object(el, "fetch_city", return_value=PAYLOAD)
    def test_calls_every_city(self, fetch):
        rows = el.extract_all(today=date(2026, 11, 22))
        self.assertEqual(fetch.call_count, len(el.CITIES))
        self.assertEqual(len(rows), 2 * len(el.CITIES))

    @mock.patch("weather.extract_load.requests.get")
    def test_request_params(self, get):
        get.return_value.json.return_value = PAYLOAD
        el.fetch_city("Jakarta", -6.2, 106.8, past_days=7)
        params = get.call_args.kwargs["params"]
        self.assertEqual(params["past_days"], 7)
        self.assertEqual(params["timezone"], "Asia/Jakarta")


if __name__ == "__main__":
    unittest.main()
