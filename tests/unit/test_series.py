from dataclasses import FrozenInstanceError
from datetime import date, timedelta

import pytest

from reorder.domain.series import ProductHistory, WeeklyPoint, weeks_with_sales

MONDAY = date(2026, 6, 29)


CUTOFF = MONDAY


def make_history(*points: tuple[date, int]) -> ProductHistory:
    return ProductHistory(
        sku="A-100",
        points=tuple(WeeklyPoint(week_start=d, qty=q) for d, q in points),
        last_sale_date=None,
        last_purchase_date=None,
    )


def weeks_before_cutoff(weeks: int) -> date:
    return CUTOFF - timedelta(weeks=weeks)


def test_weeks_with_sales_skips_zero_quantity_weeks() -> None:
    history = make_history((weeks_before_cutoff(2), 4), (weeks_before_cutoff(1), 0))
    assert [w.qty for w in weeks_with_sales(history, CUTOFF)] == [4]


def test_weeks_with_sales_of_empty_history_is_empty() -> None:
    assert weeks_with_sales(make_history(), CUTOFF) == []


def test_weeks_with_sales_includes_first_week_of_window() -> None:
    history = make_history((weeks_before_cutoff(52), 4))
    assert len(weeks_with_sales(history, CUTOFF)) == 1


def test_weeks_with_sales_excludes_week_before_window() -> None:
    history = make_history((weeks_before_cutoff(53), 4))
    assert weeks_with_sales(history, CUTOFF) == []


def test_weeks_with_sales_excludes_week_starting_on_cutoff() -> None:
    history = make_history((CUTOFF, 4))
    assert weeks_with_sales(history, CUTOFF) == []


def test_weeks_with_sales_sorts_oldest_first() -> None:
    history = make_history((weeks_before_cutoff(1), 8), (weeks_before_cutoff(3), 4))
    assert [w.qty for w in weeks_with_sales(history, CUTOFF)] == [4, 8]


def test_weeks_with_sales_uses_custom_window() -> None:
    history = make_history((weeks_before_cutoff(5), 4), (weeks_before_cutoff(4), 8))
    assert [w.qty for w in weeks_with_sales(history, CUTOFF, window_weeks=4)] == [8]


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
