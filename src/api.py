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


ENDPOINTS = [
    ("/reports/by-province", "Crime totals by province"),
    ("/reports/by-year", "Crime totals by year"),
    ("/reports/by-province-year", "Crime totals by province and year"),
    ("/reports/top-categories", "Top 5 crime categories nationally"),
    ("/reports/top-category-per-province", "Top category per province"),
    ("/reports/year-over-year", "Year-over-year change per province"),
]


@app.get("/")
def index():
    links = "".join(
        f'<li><a href="{path}"><code>{path}</code></a> — {desc}</li>'
        for path, desc in ENDPOINTS
    )
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Crime Data Pipeline API</title>
        <style>
            body {{ font-family: -apple-system, Segoe UI, Roboto, sans-serif;
                    max-width: 640px; margin: 60px auto; padding: 0 20px;
                    background: #0f172a; color: #e2e8f0; }}
            h1 {{ font-size: 1.6rem; margin-bottom: 4px; }}
            p.subtitle {{ color: #94a3b8; margin-top: 0; }}
            ul {{ list-style: none; padding: 0; }}
            li {{ background: #1e293b; margin: 10px 0; padding: 14px 18px;
                  border-radius: 8px; }}
            a {{ color: #38bdf8; text-decoration: none; font-weight: 600; }}
            a:hover {{ text-decoration: underline; }}
            code {{ font-size: 0.95rem; }}
        </style>
    </head>
    <body>
        <h1>Crime Data Pipeline API</h1>
        <p class="subtitle">South African crime statistics — extracted, cleaned, loaded into PostgreSQL, served as JSON.</p>
        <ul>{links}</ul>
    </body>
    </html>
    """


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
