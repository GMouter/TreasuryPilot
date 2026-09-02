from datetime import date

import pytest

from app.services import rates


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self.payload


class FakeClient:
    def __init__(self, response):
        self.response = response

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        pass

    def get(self, *_args, **_kwargs):
        return self.response


def test_historical_rates_parse_time_series(monkeypatch):
    response = FakeResponse({
        "rates": {
            "2026-01-02": {"GBP": 0.79},
            "2026-01-05": {"GBP": 0.81},
        },
    })
    monkeypatch.setattr(rates.httpx, "Client", lambda **_kwargs: FakeClient(response))

    result = rates.get_historical_fx_rates(
        "usd",
        "gbp",
        date(2026, 1, 1),
        date(2026, 1, 5),
    )

    assert result == [
        {"currency": "USD", "base_currency": "GBP", "rate": 0.79, "date": "2026-01-02"},
        {"currency": "USD", "base_currency": "GBP", "rate": 0.81, "date": "2026-01-05"},
    ]


def test_historical_rates_reject_reversed_date_range():
    with pytest.raises(ValueError, match="Start date"):
        rates.get_historical_fx_rates(
            "USD",
            "GBP",
            date(2026, 2, 1),
            date(2026, 1, 1),
        )
