
from datetime import datetime
from decimal import Decimal

import polars as pl
import psycopg

from load import load_trips, load_zones


def test_copy_rollback_and_trip_append():

    trips = pl.DataFrame({
        "vendor_id": [1],
        "pickup_datetime": [datetime(2024, 1, 1, 9, 0)],
        "dropoff_datetime": [datetime(2024, 1, 1, 9, 10)],
        "passenger_count": [1],
        "trip_distance": [2.5],
        "pickup_location_id": [999],
        "dropoff_location_id": [1],
        "payment_type": [1],
        "fare_amount": [Decimal("10.00")],
        "tip_amount": [Decimal("2.00")],
        "total_amount": [Decimal("12.00")]
    })

    with psycopg.connect(autocommit=True) as conn:

        before = conn.execute(
            "SELECT COUNT(*) FROM raw.yellow_taxi_trips"
        ).fetchone()[0]

        with conn.transaction(force_rollback=True):

            assert load_trips(conn, trips) == 1
            assert load_trips(conn, trips) == 1

            inside = conn.execute(
                "SELECT COUNT(*) FROM raw.yellow_taxi_trips"
            ).fetchone()[0]

            assert inside == before + 2

        after = conn.execute(
            "SELECT COUNT(*) FROM raw.yellow_taxi_trips"
        ).fetchone()[0]

        assert after == before


def test_repeated_zone_loads_are_safe():

    zones = [
        (999, "Test Borough", "Test Zone", "Test Service")
    ]

    with psycopg.connect(autocommit=True) as conn:

        with conn.transaction(force_rollback=True):

            assert load_zones(conn, zones) == 1
            assert load_zones(conn, zones) == 1

            result = conn.execute(
                """
                SELECT COUNT(*)
                FROM raw.taxi_zones
                WHERE location_id = 999
                """
            ).fetchone()[0]

            assert result == 1

