"""
Minimal REST API serving the crime data reports as JSON.
"""

from flask import Flask, jsonify

from src.config import load_config
from src.load import get_connection

app = Flask(__name__)


def run_query(sql: str) -> list[dict]:
    """Run a query against the configured DB and return rows as a list of dicts."""
    config = load_config()
    conn = get_connection(config.db)
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            columns = [desc[0] for desc in cur.description]
            rows = cur.fetchall()
            return [dict(zip(columns, row)) for row in rows]
    finally:
        conn.close()


@app.get("/")
def index():
    return jsonify({
        "service": "crime-data-pipeline API",
        "endpoints": [
            "/reports/by-province",
            "/reports/by-year",
            "/reports/by-province-year",
            "/reports/top-categories",
            "/reports/top-category-per-province",
            "/reports/year-over-year",
        ],
    })


@app.get("/reports/by-province")
def by_province():
    rows = run_query("""
        SELECT p.name AS province, SUM(c.count) AS total_crimes
        FROM crimes c
        JOIN provinces p ON p.id = c.province_id
        GROUP BY p.name
        ORDER BY total_crimes DESC
    """)
    return jsonify(rows)


@app.get("/reports/by-year")
def by_year():
    rows = run_query("""
        SELECT y.year, SUM(c.count) AS total_crimes
        FROM crimes c
        JOIN years y ON y.id = c.year_id
        GROUP BY y.year
        ORDER BY y.year
    """)
    return jsonify(rows)


@app.get("/reports/by-province-year")
def by_province_year():
    rows = run_query("""
        SELECT p.name AS province, y.year, SUM(c.count) AS total_crimes
        FROM crimes c
        JOIN provinces p ON p.id = c.province_id
        JOIN years y ON y.id = c.year_id
        GROUP BY p.name, y.year
        ORDER BY p.name, y.year
    """)
    return jsonify(rows)


@app.get("/reports/top-categories")
def top_categories():
    rows = run_query("""
        SELECT c.category, SUM(c.count) AS total_crimes
        FROM crimes c
        GROUP BY c.category
        ORDER BY total_crimes DESC
        LIMIT 5
    """)
    return jsonify(rows)


@app.get("/reports/top-category-per-province")
def top_category_per_province():
    rows = run_query("""
        WITH latest_year AS (
            SELECT MAX(year) AS year FROM years
        )
        SELECT DISTINCT ON (p.name)
            p.name AS province, c.category, c.count
        FROM crimes c
        JOIN provinces p ON p.id = c.province_id
        JOIN years y ON y.id = c.year_id
        JOIN latest_year ly ON y.year = ly.year
        ORDER BY p.name, c.count DESC
    """)
    return jsonify(rows)


@app.get("/reports/year-over-year")
def year_over_year():
    rows = run_query("""
        SELECT
            p.name AS province,
            y.year,
            SUM(c.count) AS total_crimes,
            SUM(c.count) - LAG(SUM(c.count)) OVER (
                PARTITION BY p.name ORDER BY y.year
            ) AS change_from_prev_year
        FROM crimes c
        JOIN provinces p ON p.id = c.province_id
        JOIN years y ON y.id = c.year_id
        GROUP BY p.name, y.year
        ORDER BY p.name, y.year
    """)
    return jsonify(rows)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
