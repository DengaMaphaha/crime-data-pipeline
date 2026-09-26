# South African Crime Data Pipeline

CSV/API -> Python -> PostgreSQL. Cleans province/year/category/count fields,
loads them into a normalised schema, and produces SQL reports such as crime
totals by province.

## Schema

- provinces(id, name)
- years(id, year)
- crimes(id, province_id, year_id, category, count)

## Setup

    python -m venv .venv
    .venv\Scripts\Activate.ps1
    pip install -r requirements.txt
    copy .env.example .env

## Run

    python -m src.pipeline

## Reports

    psql -d crime_data -f sql/reports.sql

## Tests

    pytest

##  Verification code: WTC-6VL5YFJG
