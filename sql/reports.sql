-- SQL reports for the crime data warehouse.
-- Run with: psql -d crime_data -f sql/reports.sql

-- 1. Crime totals by province (all years combined)
SELECT
    p.name AS province,
    SUM(c.count) AS total_crimes
FROM crimes c
JOIN provinces p ON p.id = c.province_id
GROUP BY p.name
ORDER BY total_crimes DESC;

-- 2. Crime totals by year (all provinces combined)
SELECT
    y.year,
    SUM(c.count) AS total_crimes
FROM crimes c
JOIN years y ON y.id = c.year_id
GROUP BY y.year
ORDER BY y.year;

-- 3. Crime totals by province and year
SELECT
    p.name AS province,
    y.year,
    SUM(c.count) AS total_crimes
FROM crimes c
JOIN provinces p ON p.id = c.province_id
JOIN years y ON y.id = c.year_id
GROUP BY p.name, y.year
ORDER BY p.name, y.year;

-- 4. Top 5 crime categories nationally
SELECT
    c.category,
    SUM(c.count) AS total_crimes
FROM crimes c
GROUP BY c.category
ORDER BY total_crimes DESC
LIMIT 5;

-- 5. Top crime category per province (most recent year on record)
WITH latest_year AS (
    SELECT MAX(year) AS year FROM years
)
SELECT DISTINCT ON (p.name)
    p.name AS province,
    c.category,
    c.count
FROM crimes c
JOIN provinces p ON p.id = c.province_id
JOIN years y ON y.id = c.year_id
JOIN latest_year ly ON y.year = ly.year
ORDER BY p.name, c.count DESC;

-- 6. Year-over-year change in total crimes per province
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
ORDER BY p.name, y.year;
