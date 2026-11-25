
import csv
import shutil
import tempfile
import urllib.request
from pathlib import Path

import polars as pl


def download_file(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)

    temp_path = None

    try:
        with tempfile.NamedTemporaryFile(
            dir=destination.parent,
            suffix=".tmp",
            delete=False
        ) as temp:
            temp_path = Path(temp.name)

        with urllib.request.urlopen(url, timeout=120) as response:
            with temp_path.open("wb") as output:
                shutil.copyfileobj(response, output)

        temp_path.replace(destination)

    finally:
        if temp_path is not None and temp_path.exists():
            temp_path.unlink()


def extract_trips(
    source: Path,
    *,
    month: str,
    download: bool
) -> pl.DataFrame:

    if not source.exists():
        if not download:
            raise FileNotFoundError(
                f"Explicit trip source does not exist: {source}"
            )

        url = (
            "https://d37ci6vzurychx.cloudfront.net/"
            f"trip-data/yellow_tripdata_{month}.parquet"
        )

        download_file(url, source)

    return pl.read_parquet(source)


def extract_zones(
    source: Path,
    *,
    download: bool
) -> list[tuple]:

    if not source.exists():
        if not download:
            raise FileNotFoundError(
                f"Zone source does not exist: {source}"
            )

        url = (
            "https://d37ci6vzurychx.cloudfront.net/"
            "misc/taxi_zone_lookup.csv"
        )

        download_file(url, source)

    zones = []

    with source.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            zones.append((
                int(row["LocationID"]),
                row["Borough"],
                row["Zone"],
                row["service_zone"] or None
            ))

    return zones
