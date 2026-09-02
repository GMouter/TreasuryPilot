from datetime import date
from types import SimpleNamespace

from app.routers import exposures as exposure_routes
from app.models.company import Company


class FakeQuery:
    def __init__(self, record=None, records=None):
        self.record = record
        self.records = records or []

    def filter(self, *_conditions):
        return self

    def first(self):
        return self.record

    def all(self):
        return self.records


class FakeSession:
    def __init__(self, record=None, records=None):
        self.query_result = FakeQuery(record=record, records=records)
        self.deleted = None
        self.committed = False

    def query(self, *_models):
        if _models == (Company,):
            return FakeQuery(record=SimpleNamespace(id=1, base_currency="GBP"))
        return self.query_result

    def delete(self, record):
        self.deleted = record

    def commit(self):
        self.committed = True

    def refresh(self, _record):
        pass


def test_empty_summary_returns_usable_portfolio():
    result = exposure_routes.get_exposure_summary(1, FakeSession())

    assert result["portfolio"]["total_exposures"] == 0
    assert result["risk"]["overall_score"] == 0
    assert result["portfolio_recommendation"]["priority_exposure"] is None
    assert result["exposures"] == []


def test_delete_exposure_removes_existing_record():
    record = SimpleNamespace(id=7)
    session = FakeSession(record=record)

    result = exposure_routes.delete_exposure(7, session)

    assert result is None
    assert session.deleted is record
    assert session.committed is True


def test_update_exposure_refreshes_rate_and_fields(monkeypatch):
    record = SimpleNamespace(
        id=7,
        company_id=1,
        currency="USD",
        foreign_amount=100,
        current_fx_rate=1.2,
        payment_date=date(2026, 12, 1),
        hedge_percentage=50,
    )
    session = FakeSession(record=record)
    monkeypatch.setattr(
        exposure_routes,
        "get_fx_rate",
        lambda currency, base_currency: {"rate": 1.25},
    )

    request = exposure_routes.ExposureUpdate(
        currency="eur",
        foreign_amount=250,
        payment_date=date(2027, 1, 15),
        hedge_percentage=80,
    )
    result = exposure_routes.update_exposure(7, request, session)

    assert result is record
    assert record.currency == "EUR"
    assert record.foreign_amount == 250
    assert record.current_fx_rate == 1.25
    assert record.payment_date == date(2027, 1, 15)
    assert record.hedge_percentage == 80
    assert session.committed is True
