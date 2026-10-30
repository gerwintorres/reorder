from datetime import date, timedelta
from decimal import Decimal

import pytest

from reorder.domain.classification import (
    AbcClass,
    ProductTotals,
    abc_scores,
    class_for_share,
    classify_abc,
    recency_factor,
)

CUTOFF = date(2026, 6, 29)
RECENT_SALE = CUTOFF - timedelta(days=7)


def product(
    sku: str,
    size: int,
    *,
    profit: int | None = None,
    last_sale_date: date | None = RECENT_SALE,
) -> ProductTotals:
    # Revenue, profit and weeks grow together, so the score follows `size`.
    return ProductTotals(
        sku=sku,
        revenue=Decimal(size * 1000),
        profit=Decimal(size * 100 if profit is None else profit),
        weeks_with_sales=size,
        last_sale_date=last_sale_date,
    )


def test_three_products_fall_in_a_b_and_c() -> None:
    # Cumulative shares: 54.6 %, 84.7 %, 100 %.
    products = [product("A-1", 50), product("B-1", 25), product("C-1", 10)]
    assert classify_abc(products, CUTOFF) == {
        "A-1": AbcClass.A,
        "B-1": AbcClass.B,
        "C-1": AbcClass.C,
    }


def test_top_product_is_a_even_above_seventy_percent() -> None:
    # The top product alone holds 89.4 % of the total score.
    products = [product("BIG", 50), product("SMALL", 1)]
    assert classify_abc(products, CUTOFF)["BIG"] is AbcClass.A


def test_negative_profit_is_c_even_with_the_highest_revenue() -> None:
    products = [product("LOSS", 52, profit=-1), product("OK", 10)]
    assert classify_abc(products, CUTOFF) == {"LOSS": AbcClass.C, "OK": AbcClass.A}


def test_all_products_are_c_when_every_score_is_zero() -> None:
    products = [
        product("X", 0, last_sale_date=None),
        product("Y", 0, last_sale_date=None),
    ]
    assert set(classify_abc(products, CUTOFF).values()) == {AbcClass.C}


def test_zero_profit_everywhere_does_not_break_normalization() -> None:
    products = [product("A-1", 50, profit=0), product("B-1", 25, profit=0)]
    assert classify_abc(products, CUTOFF)["A-1"] is AbcClass.A


def test_ties_are_ranked_by_sku_whatever_the_input_order() -> None:
    first = classify_abc([product("Y", 10), product("X", 10)], CUTOFF)
    second = classify_abc([product("X", 10), product("Y", 10)], CUTOFF)
    assert first == second == {"X": AbcClass.A, "Y": AbcClass.C}


def test_empty_collection_has_no_classes() -> None:
    assert classify_abc([], CUTOFF) == {}


@pytest.mark.parametrize(
    ("share", "expected"),
    [
        (0.70, AbcClass.A),
        (0.7001, AbcClass.B),
        (0.90, AbcClass.B),
        (0.9001, AbcClass.C),
    ],
)
def test_class_for_share_boundaries(share: float, expected: AbcClass) -> None:
    assert class_for_share(share) is expected


@pytest.mark.parametrize(
    ("days", "expected"),
    [(0, 1.0), (60, 1.0), (61, 0.5), (90, 0.5), (91, 0.0)],
)
def test_recency_factor_by_days_since_last_sale(days: int, expected: float) -> None:
    assert recency_factor(CUTOFF - timedelta(days=days), CUTOFF) == expected


def test_recency_factor_without_last_sale_is_zero() -> None:
    assert recency_factor(None, CUTOFF) == 0.0


def test_abc_score_weights_each_factor() -> None:
    top = product("TOP", 52)
    other = ProductTotals(
        sku="OTHER",
        revenue=Decimal(100_000),
        profit=Decimal(2_600),
        weeks_with_sales=13,
        last_sale_date=CUTOFF - timedelta(days=75),
    )
    # 0.9 * (0.5 * 1.0 + 0.3 * 0.5 + 0.2 * 0.25) + 0.1 * 0.5
    assert abc_scores([top, other], CUTOFF)["OTHER"] == pytest.approx(0.68)


def test_zero_profit_is_ranked_not_forced_to_c() -> None:
    products = [product("ZERO", 50, profit=0), product("SMALL", 1)]
    assert classify_abc(products, CUTOFF)["ZERO"] is AbcClass.A
