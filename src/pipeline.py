"""
Entry point: extract -> transform -> load.

    python -m src.pipeline

Reads its settings from config.load_config() (env vars / .env). Bad rows are
reported but do not stop the run - everything that *can* be cleaned still
gets loaded.
"""

import sys

from src.config import load_config
from src.extract import extract
from src.load import create_schema, get_connection, load_records
from src.transform import clean_rows


def run() -> int:
    config = load_config()

    print(f"Extracting from '{config.source}'...")
    raw_records = extract(config.source, config.csv_path, config.api_url)
    print(f"  {len(raw_records)} raw records")

    cleaned, errors = clean_rows(raw_records)
    print(f"Cleaned {len(cleaned)} records, {len(errors)} rejected")
    for error in errors:
        print(f"  skipped: {error} | row={error.row}", file=sys.stderr)

    conn = get_connection(config.db)
    try:
        create_schema(conn)
        written = load_records(conn, cleaned)
        print(f"Loaded {written} records into PostgreSQL")
    finally:
        conn.close()

    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(run())
