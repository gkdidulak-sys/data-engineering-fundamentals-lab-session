
import argparse
import os
import sys
import time
from datetime import date
from pathlib import Path

import psycopg

from extract import extract_trips, extract_zones
from load import load_trips, load_zones
from transform import clean_trips


DEFAULT_MONTH = "2024-01"
DEFAULT_DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def parse_month(value: str) -> str:
    try:
        date.fromisoformat(f"{value}-01")
    except ValueError:
        raise argparse.ArgumentTypeError(
            "month must be in YYYY-MM format"
        ) from None

    return value


def parse_args(argv=None):

    parser = argparse.ArgumentParser(
        description="Load NYC Yellow Taxi data."
    )

    parser.add_argument(
        "--month",
        type=parse_month,
        default=DEFAULT_MONTH
    )

    parser.add_argument(
        "--data-dir",
        type=Path,
        default=os.environ.get("TAXI_DATA_DIR") or DEFAULT_DATA_DIR
    )

    parser.add_argument(
        "--source",
        type=Path,
        help="Use an existing local Parquet file"
    )

    parser.add_argument(
    "--zones-only",
    action="store_true",
    help="Load only taxi zones and skip trip ingestion",
)

    args = parser.parse_args(argv)

    if not args.data_dir.is_absolute():
        parser.error("The data directory must be absolute")

    args.download = args.source is None

    if args.download:
        args.source = (
            args.data_dir
            / "raw"
            / "yellow_taxi"
            / f"yellow_tripdata_{args.month}.parquet"
        )
    else:
        args.source = args.source.resolve()

    args.zones_source = (
        args.data_dir
        / "raw"
        / "reference"
        / "taxi_zone_lookup.csv"
    )

    return args


def run(args):

    start = time.time()

    zones = extract_zones(
        args.zones_source,
        download=True
    )

    if args.zones_only:
        with psycopg.connect(connect_timeout=10) as conn:
            inserted_zones = load_zones(conn, zones)

        print(f"Zone source rows: {len(zones)}")
        print(f"Zones processed: {inserted_zones}")

        return

    source = extract_trips(
        args.source,
        month=args.month,
        download=args.download
    )

    trips = clean_trips(source)

    with psycopg.connect(connect_timeout=10) as conn:
        inserted_zones = load_zones(conn, zones)
        inserted_trips = load_trips(conn, trips)

    print(f"Trip source rows: {source.height}")
    print(f"Accepted trip rows: {trips.height}")
    print(f"Inserted trip rows: {inserted_trips}")
    print(f"Zone source rows: {len(zones)}")
    print(f"Zones processed: {inserted_zones}")
    print(f"Rejected trip rows: {source.height - trips.height}")
    print(f"Time taken: {time.time() - start:.2f} seconds")


def main():

    try:
        run(parse_args())
    except (NotImplementedError, FileNotFoundError) as error:
        print(error, file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

