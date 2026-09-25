"""
Gets the raw crime records, either from a local CSV file or a JSON API, and
returns them as a list of plain dicts. Nothing here is cleaned or validated
yet - that is transform.py's job.
"""

from typing import Any

import pandas as pd
import requests


def extract_from_csv(path: str) -> list[dict[str, Any]]:
    df = pd.read_csv(path)
    return df.to_dict(orient="records")


def extract_from_api(url: str, timeout: int = 30) -> list[dict[str, Any]]:
    """
    Expects the API to return a JSON array of objects, or an object with a
    top-level "results" or "data" array (both are common in public data
    portals). Raises requests.HTTPError on a non-2xx response.
    """
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    payload = response.json()

    if isinstance(payload, list):
        return payload

    for key in ("results", "data"):
        if isinstance(payload, dict) and isinstance(payload.get(key), list):
            return payload[key]

    raise ValueError(
        "Could not find a list of records in the API response "
        "(expected a JSON array, or an object with a 'results' or 'data' array)"
    )


def extract(source: str, csv_path: str, api_url: str) -> list[dict[str, Any]]:
    if source == "csv":
        return extract_from_csv(csv_path)
    if source == "api":
        return extract_from_api(api_url)
    raise ValueError(f"Unknown source '{source}'")
