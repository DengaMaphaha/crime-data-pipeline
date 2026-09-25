"""
Loads cleaned crime records into PostgreSQL.

Schema (normalised, so province/year names are stored once each):

    provinces(id, name UNIQUE)
    years(id, year UNIQUE)
    crimes(id, province_id -> provinces, year_id -> years, category, count,
           UNIQUE(province_id, year_id, category))

load_records() is idempotent: re-running it with the same input upserts
rather than duplicating rows, so the pipeline can be re-run safely (e.g.
after fixing a bad CSV and re-extracting).
"""

from typing import Any

import psycopg2
import psycopg2.extensions

from src.config import DbConfig

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS provinces (
    id   SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS years (
    id   SERIAL PRIMARY KEY,
    year INTEGER NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS crimes (
    id          SERIAL PRIMARY KEY,
    province_id INTEGER NOT NULL REFERENCES provinces(id),
    year_id     INTEGER NOT NULL REFERENCES years(id),
    category    TEXT NOT NULL,
    count       INTEGER NOT NULL CHECK (count >= 0),
    UNIQUE (province_id, year_id, category)
);

CREATE INDEX IF NOT EXISTS idx_crimes_province ON crimes(province_id);
CREATE INDEX IF NOT EXISTS idx_crimes_year ON crimes(year_id);
"""


def get_connection(db: DbConfig) -> psycopg2.extensions.connection:
    return psycopg2.connect(db.dsn)


def create_schema(conn: psycopg2.extensions.connection) -> None:
    with conn.cursor() as cur:
        cur.execute(SCHEMA_SQL)
    conn.commit()


def _get_or_create_province(cur, name: str, cache: dict[str, int]) -> int:
    if name in cache:
        return cache[name]
    cur.execute(
        """
        INSERT INTO provinces (name) VALUES (%s)
        ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
        RETURNING id
        """,
        (name,),
    )
    province_id = cur.fetchone()[0]
    cache[name] = province_id
    return province_id


def _get_or_create_year(cur, year: int, cache: dict[int, int]) -> int:
    if year in cache:
        return cache[year]
    cur.execute(
        """
        INSERT INTO years (year) VALUES (%s)
        ON CONFLICT (year) DO UPDATE SET year = EXCLUDED.year
        RETURNING id
        """,
        (year,),
    )
    year_id = cur.fetchone()[0]
    cache[year] = year_id
    return year_id


def load_records(
    conn: psycopg2.extensions.connection, records: list[dict[str, Any]]
) -> int:
    """
    Upserts cleaned records (as produced by transform.clean_rows) into the
    crimes table, creating any new province/year rows it needs along the
    way. Returns the number of records written.
    """
    province_cache: dict[str, int] = {}
    year_cache: dict[int, int] = {}
    written = 0

    with conn.cursor() as cur:
        for record in records:
            province_id = _get_or_create_province(cur, record["province"], province_cache)
            year_id = _get_or_create_year(cur, record["year"], year_cache)

            cur.execute(
                """
                INSERT INTO crimes (province_id, year_id, category, count)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (province_id, year_id, category)
                DO UPDATE SET count = EXCLUDED.count
                """,
                (province_id, year_id, record["category"], record["count"]),
            )
            written += 1

    conn.commit()
    return written
