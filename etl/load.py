import polars as pl
from psycopg import Connection


def load_trips(conn: Connection, trips: pl.DataFrame) -> int:
    """Append accepted trips and return the number written."""
    # TODO: Write the selected columns to raw.yellow_taxi_trips. The pipeline
    # owns the transaction. PostgreSQL generates the trip_id for each row.
    raise NotImplementedError("Load TODO: append accepted trips to PostgreSQL.")
