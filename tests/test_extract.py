import pytest
import requests

from src.extract import extract, extract_from_api, extract_from_csv


# -- CSV ---------------------------------------------------------

def test_extract_from_csv(tmp_path):
    csv_path = tmp_path / "sample.csv"
    csv_path.write_text(
        "province,year,category,count\n"
        "Gauteng,2019,murder,100\n"
        "Western Cape,2018,robbery,50\n"
    )

    records = extract_from_csv(str(csv_path))

    assert records == [
        {"province": "Gauteng", "year": 2019, "category": "murder", "count": 100},
        {"province": "Western Cape", "year": 2018, "category": "robbery", "count": 50},
    ]


def test_extract_dispatches_to_csv(tmp_path):
    csv_path = tmp_path / "sample.csv"
    csv_path.write_text("province,year,category,count\nGauteng,2019,murder,100\n")

    records = extract("csv", str(csv_path), api_url="")

    assert records == [{"province": "Gauteng", "year": 2019, "category": "murder", "count": 100}]


def test_extract_unknown_source_raises():
    with pytest.raises(ValueError):
        extract("xml", csv_path="whatever.csv", api_url="")


# -- API ---------------------------------------------------------

class _FakeResponse:
    def __init__(self, payload, status_ok=True):
        self._payload = payload
        self._status_ok = status_ok

    def raise_for_status(self):
        if not self._status_ok:
            raise requests.HTTPError("boom")

    def json(self):
        return self._payload


def test_extract_from_api_top_level_list(monkeypatch):
    payload = [{"province": "Gauteng", "year": 2019, "category": "murder", "count": 100}]
    monkeypatch.setattr(requests, "get", lambda *a, **k: _FakeResponse(payload))

    assert extract_from_api("http://example.test/data") == payload


@pytest.mark.parametrize("key", ["results", "data"])
def test_extract_from_api_wrapped_in_object(monkeypatch, key):
    records = [{"province": "Gauteng", "year": 2019, "category": "murder", "count": 100}]
    monkeypatch.setattr(requests, "get", lambda *a, **k: _FakeResponse({key: records}))

    assert extract_from_api("http://example.test/data") == records


def test_extract_from_api_unrecognised_shape_raises(monkeypatch):
    monkeypatch.setattr(requests, "get", lambda *a, **k: _FakeResponse({"nope": []}))

    with pytest.raises(ValueError):
        extract_from_api("http://example.test/data")


def test_extract_from_api_raises_on_http_error(monkeypatch):
    monkeypatch.setattr(
        requests, "get", lambda *a, **k: _FakeResponse(None, status_ok=False)
    )

    with pytest.raises(requests.HTTPError):
        extract_from_api("http://example.test/data")
