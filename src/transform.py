"""
Cleans raw crime records into a consistent shape:

    {"province": str, "year": int, "category": str, "count": int}

Handles the messiness real data tends to have: inconsistent casing and
spacing in province and category names, province abbreviations, and blank
or non-numeric counts.
"""

from typing import Any

# Canonical province names, keyed by every lowercase spelling / abbreviation
# we expect to see. Extend this as new variants turn up in real data.
_PROVINCE_ALIASES: dict[str, str] = {
    "western cape": "Western Cape",
    "w cape": "Western Cape",
    "wc": "Western Cape",
    "eastern cape": "Eastern Cape",
    "e cape": "Eastern Cape",
    "ec": "Eastern Cape",
    "northern cape": "Northern Cape",
    "n cape": "Northern Cape",
    "nc": "Northern Cape",
    "gauteng": "Gauteng",
    "gp": "Gauteng",
    "kwazulu-natal": "KwaZulu-Natal",
    "kwazulu natal": "KwaZulu-Natal",
    "kzn": "KwaZulu-Natal",
    "free state": "Free State",
    "fs": "Free State",
    "limpopo": "Limpopo",
    "lp": "Limpopo",
    "mpumalanga": "Mpumalanga",
    "mp": "Mpumalanga",
    "north west": "North West",
    "north-west": "North West",
    "nw": "North West",
}

MIN_YEAR = 1994  # first year of post-apartheid SAPS reporting
MAX_YEAR = 2100  # generous upper bound; catches obvious typos like "20223"


class RowError(ValueError):
    """A single input row could not be cleaned. Carries the original row for logging."""

    def __init__(self, message: str, row: dict[str, Any]):
        super().__init__(message)
        self.row = row


def clean_province(raw: Any) -> str:
    if raw is None:
        raise RowError("province is missing", {"province": raw})

    text = str(raw).strip()
    if not text:
        raise RowError("province is blank", {"province": raw})

    canonical = _PROVINCE_ALIASES.get(text.lower())
    if canonical is None:
        raise RowError(f"unrecognised province '{text}'", {"province": raw})

    return canonical


def clean_year(raw: Any) -> int:
    try:
        year = int(str(raw).strip())
    except (TypeError, ValueError):
        raise RowError(f"year is not a whole number: {raw!r}", {"year": raw}) from None

    if not (MIN_YEAR <= year <= MAX_YEAR):
        raise RowError(f"year {year} is out of range", {"year": raw})

    return year


def clean_category(raw: Any) -> str:
    if raw is None:
        raise RowError("category is missing", {"category": raw})

    text = " ".join(str(raw).split())  # trims and collapses internal whitespace
    if not text:
        raise RowError("category is blank", {"category": raw})

    return text.title()


def clean_count(raw: Any) -> int:
    if raw is None or (isinstance(raw, float) and raw != raw):  # NaN check without numpy
        raise RowError("count is missing", {"count": raw})

    text = str(raw).strip().replace(",", "")
    if not text:
        raise RowError("count is blank", {"count": raw})

    try:
        count = int(float(text))  # float() first, so "120.0" from CSV parsing also works
    except ValueError:
        raise RowError(f"count is not a number: {raw!r}", {"count": raw}) from None

    if count < 0:
        raise RowError(f"count cannot be negative: {count}", {"count": raw})

    return count


def clean_row(row: dict[str, Any]) -> dict[str, Any]:
    """Raises RowError on the first problem found in the row."""
    return {
        "province": clean_province(row.get("province")),
        "year": clean_year(row.get("year")),
        "category": clean_category(row.get("category")),
        "count": clean_count(row.get("count")),
    }


def clean_rows(
    rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[RowError]]:
    """Cleans every row; bad rows are skipped and returned separately, not silently dropped."""
    cleaned: list[dict[str, Any]] = []
    errors: list[RowError] = []

    for row in rows:
        try:
            cleaned.append(clean_row(row))
        except RowError as error:
            error.row = row
            errors.append(error)

    return cleaned, errors
