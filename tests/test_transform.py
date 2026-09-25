import pytest

from src.transform import (
    RowError,
    clean_category,
    clean_count,
    clean_province,
    clean_row,
    clean_rows,
    clean_year,
)


# -- province ---------------------------------------------------------

@pytest.mark.parametrize(
    "raw,expected",
    [
        ("Western Cape", "Western Cape"),
        (" Western Cape ", "Western Cape"),
        ("western cape", "Western Cape"),
        ("wc", "Western Cape"),
        ("KZN", "KwaZulu-Natal"),
        ("kwazulu natal", "KwaZulu-Natal"),
        ("gp", "Gauteng"),
    ],
)
def test_clean_province_valid(raw, expected):
    assert clean_province(raw) == expected


@pytest.mark.parametrize("raw", [None, "", "   ", "Narnia"])
def test_clean_province_invalid(raw):
    with pytest.raises(RowError):
        clean_province(raw)


# -- year ---------------------------------------------------------

@pytest.mark.parametrize("raw,expected", [(2018, 2018), ("2018", 2018), (" 2020 ", 2020)])
def test_clean_year_valid(raw, expected):
    assert clean_year(raw) == expected


@pytest.mark.parametrize("raw", ["not a year", 1800, 3000, None])
def test_clean_year_invalid(raw):
    with pytest.raises(RowError):
        clean_year(raw)


# -- category ---------------------------------------------------------

@pytest.mark.parametrize(
    "raw,expected",
    [
        ("murder", "Murder"),
        ("  sexual   offences ", "Sexual Offences"),
        ("robbery with aggravating circumstances", "Robbery With Aggravating Circumstances"),
    ],
)
def test_clean_category_valid(raw, expected):
    assert clean_category(raw) == expected


@pytest.mark.parametrize("raw", [None, "", "   "])
def test_clean_category_invalid(raw):
    with pytest.raises(RowError):
        clean_category(raw)


# -- count ---------------------------------------------------------

@pytest.mark.parametrize(
    "raw,expected",
    [(3178, 3178), ("3178", 3178), ("3,178", 3178), (120.0, 120), ("120.0", 120)],
)
def test_clean_count_valid(raw, expected):
    assert clean_count(raw) == expected


@pytest.mark.parametrize("raw", [None, "", "abc", -5, float("nan")])
def test_clean_count_invalid(raw):
    with pytest.raises(RowError):
        clean_count(raw)


# -- whole row ---------------------------------------------------------

def test_clean_row_valid():
    row = {"province": " Western Cape ", "year": "2018", "category": "murder", "count": "3,178"}
    assert clean_row(row) == {
        "province": "Western Cape",
        "year": 2018,
        "category": "Murder",
        "count": 3178,
    }


def test_clean_row_raises_on_first_bad_field():
    with pytest.raises(RowError):
        clean_row({"province": "Narnia", "year": 2018, "category": "murder", "count": 5})


def test_clean_rows_separates_good_from_bad():
    rows = [
        {"province": "Gauteng", "year": 2019, "category": "murder", "count": 100},
        {"province": "Narnia", "year": 2019, "category": "murder", "count": 5},
        {"province": "Gauteng", "year": "not a year", "category": "murder", "count": 5},
    ]
    cleaned, errors = clean_rows(rows)

    assert len(cleaned) == 1
    assert cleaned[0]["province"] == "Gauteng"
    assert len(errors) == 2
    assert all(isinstance(e, RowError) for e in errors)
    # original row is preserved on the error for logging
    assert errors[0].row == rows[1]
