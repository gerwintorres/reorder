from collections.abc import Sequence
from datetime import date, timedelta

import pytest

from reorder.domain.classification import AbcClass
from reorder.domain.demand import (
    DemandEstimate,
    Rule,
    average,
    base_demand,
    efficiency,
    estimate_demand,
)
from reorder.domain.rotation import Rotation
from reorder.domain.series import ProductHistory, WeeklyPoint

CUTOFF = date(2026, 6, 29)
GOLDEN = [4, 4, 4, 12, 12, 12, 16, 20, 20, 24, 40, 52, 104]


def week(weeks_before_cutoff: int, qty: int) -> WeeklyPoint:
    return WeeklyPoint(
        week_start=CUTOFF - timedelta(weeks=weeks_before_cutoff), qty=qty
    )


def consecutive(qtys: Sequence[int]) -> tuple[WeeklyPoint, ...]:
    # Oldest first, the last one starting the week before the cutoff.
    return tuple(week(len(qtys) - i, qty) for i, qty in enumerate(qtys))


def make_history(
    points: Sequence[WeeklyPoint],
    *,
    last_sale_days: int | None = 5,
    last_purchase_days: int | None = None,
) -> ProductHistory:
    def days_ago(days: int | None) -> date | None:
        return None if days is None else CUTOFF - timedelta(days=days)

    return ProductHistory(
        sku="A-100",
        points=tuple(points),
        last_sale_date=days_ago(last_sale_days),
        last_purchase_date=days_ago(last_purchase_days),
    )


def estimate(
    history: ProductHistory,
    abc: AbcClass = AbcClass.A,
    rotation: Rotation = Rotation.MEDIUM,
) -> DemandEstimate:
    return estimate_demand(history, abc, rotation, CUTOFF)


GOLDEN_ESTIMATE = estimate(make_history(consecutive(GOLDEN)))


def test_average_of_golden_case() -> None:
    assert average(GOLDEN) == pytest.approx(24.92, abs=0.005)


def test_average_of_no_quantities_is_zero() -> None:
    assert average([]) == 0.0


def test_base_demand_keeps_an_exact_integer() -> None:
    assert base_demand(10.0, 1.64, 0.0) == 10


def test_base_demand_rounds_up() -> None:
    assert base_demand(10.01, 1.64, 0.0) == 11


def test_efficiency_of_golden_case() -> None:
    # 10 of the 13 weeks sold 37 units or less.
    assert efficiency(GOLDEN, 37) == pytest.approx(0.769, abs=0.005)


def test_efficiency_counts_weeks_equal_to_demand() -> None:
    assert efficiency([5, 10], 5) == 0.5


def test_efficiency_of_no_weeks_is_zero() -> None:
    assert efficiency([], 10) == 0.0


def test_efficiency_uses_the_final_demand() -> None:
    # The base is 37, but a stale last sale sets the demand to 0.
    result = estimate(make_history(consecutive(GOLDEN), last_sale_days=91))
    assert result.efficiency == 0.0


def test_golden_case_uses_statistical_base() -> None:
    assert GOLDEN_ESTIMATE.rule is Rule.STATISTICAL_BASE


def test_golden_case_demand_is_37() -> None:
    assert GOLDEN_ESTIMATE.demand == 37


def test_golden_case_reason_shows_average_k_and_std() -> None:
    assert GOLDEN_ESTIMATE.reason == "Average 24.92, k 1.64, std 7.25."


@pytest.mark.parametrize(
    ("field", "expected"),
    [
        ("avg", 24.92),
        ("std", 7.254),
        ("k", 1.64),
        ("base_demand", 37),
        ("efficiency", 0.769),
        ("q1", 12),
        ("q3", 24),
        ("ceiling", 36),
    ],
)
def test_golden_case_trace(field: str, expected: float) -> None:
    assert getattr(GOLDEN_ESTIMATE, field) == pytest.approx(expected, abs=0.005)


def test_golden_case_trace_lists_excluded_peaks() -> None:
    assert GOLDEN_ESTIMATE.excluded == (40, 52, 104)


def test_weeks_with_zero_qty_do_not_change_the_estimate() -> None:
    result = estimate(make_history(consecutive([*GOLDEN, 0, 0])))
    assert result.demand == 37


def test_week_outside_window_does_not_change_the_estimate() -> None:
    result = estimate(make_history((week(53, 500), *consecutive(GOLDEN))))
    assert result.demand == 37


def test_trace_has_no_ceiling_when_series_is_too_short_to_filter() -> None:
    result = estimate(make_history(consecutive([5, 9, 7])))
    assert (result.q1, result.q3, result.ceiling, result.excluded) == (
        None,
        None,
        None,
        (),
    )


def test_trace_has_ceiling_from_four_values() -> None:
    result = estimate(make_history(consecutive([10, 10, 12, 50])))
    assert (result.q1, result.ceiling, result.excluded) == (10, 33, (50,))


def test_no_sales_when_every_week_has_zero_qty() -> None:
    result = estimate(make_history(consecutive([0, 0, 0])))
    assert (result.rule, result.demand) == (Rule.NO_SALES, 0)


def test_no_sales_when_the_only_sale_is_outside_window() -> None:
    result = estimate(make_history((week(53, 9),)))
    assert (result.rule, result.demand) == (Rule.NO_SALES, 0)


def test_no_sales_trace_is_zero() -> None:
    result = estimate(make_history(()))
    assert (result.avg, result.std, result.base_demand) == (0.0, 0.0, 0)


def test_single_stale_sale_older_than_three_weeks() -> None:
    result = estimate(make_history((week(4, 9),), last_sale_days=28))
    assert (result.rule, result.demand) == (Rule.SINGLE_STALE_SALE, 0)


def test_single_sale_three_weeks_ago_is_not_stale() -> None:
    result = estimate(make_history((week(3, 9),), last_sale_days=21))
    assert (result.rule, result.demand) == (Rule.STATISTICAL_BASE, 9)


def test_two_old_sales_are_not_a_single_stale_sale() -> None:
    result = estimate(make_history((week(10, 9), week(8, 9)), last_sale_days=56))
    assert result.rule is Rule.STATISTICAL_BASE


def test_missing_last_sale_date() -> None:
    result = estimate(make_history(consecutive(GOLDEN), last_sale_days=None))
    assert (result.rule, result.demand) == (Rule.MISSING_LAST_SALE_DATE, 0)


def test_stale_last_sale_after_90_days() -> None:
    result = estimate(make_history(consecutive(GOLDEN), last_sale_days=91))
    assert (result.rule, result.demand) == (Rule.STALE_LAST_SALE, 0)


def test_stale_last_sale_reason_shows_days() -> None:
    result = estimate(make_history(consecutive(GOLDEN), last_sale_days=91))
    assert result.reason == "Last sale 91 days ago."


def test_last_sale_90_days_ago_is_capped_not_stale() -> None:
    result = estimate(make_history(consecutive(GOLDEN), last_sale_days=90))
    assert result.rule is Rule.RECENT_AVERAGE_CAP


def test_recent_average_cap_after_60_days_without_sales() -> None:
    # Average of the last 8 weeks with sales is 36, below the base of 37.
    result = estimate(make_history(consecutive(GOLDEN), last_sale_days=61))
    assert (result.rule, result.demand) == (Rule.RECENT_AVERAGE_CAP, 36)


def test_last_sale_60_days_ago_uses_statistical_base() -> None:
    result = estimate(make_history(consecutive(GOLDEN), last_sale_days=60))
    assert result.rule is Rule.STATISTICAL_BASE


def test_recent_average_cap_rounds_up() -> None:
    # The last 8 weeks average 34.875, below the base of 36.
    history = make_history(consecutive([*GOLDEN, 3]), last_sale_days=61)
    assert estimate(history).demand == 35


def test_recent_average_cap_keeps_base_when_it_is_lower() -> None:
    # Base is 12 with k 0.13; the last 8 weeks average 30.
    history = make_history(consecutive([1] * 20 + [30] * 8), last_sale_days=61)
    result = estimate(history, AbcClass.C, Rotation.LOW)
    assert (result.rule, result.demand) == (Rule.RECENT_AVERAGE_CAP, 12)


def test_recent_average_cap_after_90_days_without_purchases() -> None:
    history = make_history(consecutive(GOLDEN), last_purchase_days=91)
    result = estimate(history)
    assert (result.rule, result.demand) == (Rule.RECENT_AVERAGE_CAP, 36)


def test_last_purchase_90_days_ago_uses_statistical_base() -> None:
    history = make_history(consecutive(GOLDEN), last_purchase_days=90)
    assert estimate(history).rule is Rule.STATISTICAL_BASE


def test_no_sales_wins_over_missing_last_sale_date() -> None:
    result = estimate(make_history((), last_sale_days=None))
    assert result.rule is Rule.NO_SALES


def test_single_stale_sale_wins_over_missing_last_sale_date() -> None:
    result = estimate(make_history((week(4, 9),), last_sale_days=None))
    assert result.rule is Rule.SINGLE_STALE_SALE
