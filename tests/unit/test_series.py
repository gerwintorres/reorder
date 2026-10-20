from dataclasses import FrozenInstanceError
from datetime import date, timedelta

import pytest

from reorder.domain.series import ProductHistory, WeeklyPoint, positive_qtys

MONDAY = date(2026, 6, 29)


def make_history(*qtys: int) -> ProductHistory:
    points = tuple(
        WeeklyPoint(week_start=MONDAY + timedelta(weeks=i), qty=qty)
        for i, qty in enumerate(qtys)
    )
    return ProductHistory(
        sku="A-100", points=points, last_sale_date=None, last_purchase_date=None
    )


def test_positive_qtys_skips_zero_quantity_weeks() -> None:
    assert positive_qtys(make_history(4, 0, 12, 0, 20)) == [4, 12, 20]


def test_positive_qtys_of_empty_history_is_empty() -> None:
    assert positive_qtys(make_history()) == []


def test_weekly_point_accepts_zero_qty() -> None:
    assert WeeklyPoint(week_start=MONDAY, qty=0).qty == 0


@pytest.mark.parametrize("days_after_monday", [1, 6])
def test_weekly_point_rejects_week_start_not_on_monday(days_after_monday: int) -> None:
    with pytest.raises(ValueError, match="Monday"):
        WeeklyPoint(week_start=MONDAY + timedelta(days=days_after_monday), qty=1)


def test_weekly_point_rejects_negative_qty() -> None:
    with pytest.raises(ValueError, match="non-negative"):
        WeeklyPoint(week_start=MONDAY, qty=-1)


def test_weekly_point_rejects_bool_qty() -> None:
    with pytest.raises(ValueError, match="non-negative"):
        WeeklyPoint(week_start=MONDAY, qty=True)


def test_weekly_point_is_immutable() -> None:
    point = WeeklyPoint(week_start=MONDAY, qty=4)
    with pytest.raises(FrozenInstanceError):
        point.qty = 5  # type: ignore[misc]


@pytest.mark.parametrize("sku", ["", "   "])
def test_product_history_rejects_blank_sku(sku: str) -> None:
    with pytest.raises(ValueError, match="sku"):
        ProductHistory(sku=sku, points=(), last_sale_date=None, last_purchase_date=None)
