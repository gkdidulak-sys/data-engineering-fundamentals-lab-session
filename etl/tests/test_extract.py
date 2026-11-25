
import csv

import polars as pl
import pytest

from extract import extract_trips, extract_zones


def test_extract_trips(tmp_path):
    source = tmp_path / "trips.parquet"

    pl.DataFrame({
        "VendorID": [1],
        "fare_amount": [10.0]
    }).write_parquet(source)

    result = extract_trips(
        source,
        month="2024-01",
        download=False
    )

    assert result.height == 1


def test_missing_explicit_trip_source(tmp_path):
    source = tmp_path / "missing.parquet"

    with pytest.raises(FileNotFoundError):
        extract_trips(
            source,
            month="2024-01",
            download=False
        )


def test_extract_zones(tmp_path):
    source = tmp_path / "zones.csv"

    with source.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([
            "LocationID",
            "Borough",
            "Zone",
            "service_zone"
        ])
        writer.writerow([1, "Manhattan", "Test Zone", "Yellow"])

    result = extract_zones(source, download=False)

    assert result == [
        (1, "Manhattan", "Test Zone", "Yellow")
    ]

