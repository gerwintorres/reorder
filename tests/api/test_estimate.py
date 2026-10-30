from datetime import date, timedelta
from typing import Any

import pytest
from fastapi.testclient import TestClient

from reorder.api.main import app

client = TestClient(app)

URL = "/api/v1/estimate/preview"
GOLDEN = [4, 4, 4, 12, 12, 12, 16, 20, 20, 24, 40, 52, 104]
FIRST_WEEK = date(2026, 3, 30)


def golden_payload(**overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "sku": "A-100",
        "points": [
            {"week_start": str(FIRST_WEEK + timedelta(weeks=i)), "qty": qty}
            for i, qty in enumerate(GOLDEN)
        ],
        "abc": "A",
        "rotation": "medium",
        "last_sale_date": "2026-06-24",
        "last_purchase_date": None,
        "cutoff_date": "2026-06-29",
    }
    return payload | overrides


def test_preview_golden_case_returns_demand_37() -> None:
    response = client.post(URL, json=golden_payload())
    assert (response.status_code, response.json()["demand"]) == (200, 37)


def test_preview_returns_rule_and_reason() -> None:
    body = client.post(URL, json=golden_payload()).json()
    assert (body["rule"], body["reason"]) == (
        "statistical_base",
        "Average 24.92, k 1.64, std 7.25.",
    )


def test_preview_returns_calculation_trace() -> None:
    body = client.post(URL, json=golden_payload()).json()
    assert (body["k"], body["ceiling"], body["excluded"]) == (1.64, 36, [40, 52, 104])


def test_preview_echoes_sku() -> None:
    assert client.post(URL, json=golden_payload()).json()["sku"] == "A-100"


def test_preview_caps_demand_when_last_purchase_is_old() -> None:
    body = client.post(URL, json=golden_payload(last_purchase_date="2026-03-30")).json()
    assert (body["rule"], body["demand"]) == ("recent_average_cap", 36)


@pytest.mark.parametrize(
    "overrides",
    [
        {"abc": "D"},
        {"rotation": "fast"},
        {"cutoff_date": None},
        {"cutoff_date": "29/06/2026"},
        {"sku": ""},
        {"points": [{"week_start": "2026-06-22", "qty": -1}]},
        {"points": [{"week_start": "2026-06-22", "qty": True}]},
        {"points": [{"week_start": "2026-06-22", "qty": "4"}]},
    ],
)
def test_preview_rejects_invalid_input(overrides: dict[str, Any]) -> None:
    assert client.post(URL, json=golden_payload(**overrides)).status_code == 422


def test_docs_example_returns_demand_37() -> None:
    # The example exactly as /docs shows it, so "Try it out" works as is.
    schemas = client.get("/openapi.json").json()["components"]["schemas"]
    example = schemas["EstimatePreviewIn"]["examples"][0]
    response = client.post(URL, json=example)
    assert (response.status_code, response.json()["demand"]) == (200, 37)


def test_preview_accepts_missing_optional_dates() -> None:
    payload = golden_payload()
    del payload["last_purchase_date"]
    assert client.post(URL, json=payload).status_code == 200
