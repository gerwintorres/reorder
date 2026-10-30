from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import StrEnum

REVENUE_WEIGHT = 0.50
PROFIT_WEIGHT = 0.30
WEEKS_WEIGHT = 0.20
BASE_WEIGHT = 0.90
RECENCY_WEIGHT = 0.10
FULL_RECENCY_DAYS = 60
HALF_RECENCY_DAYS = 90
A_SHARE = 0.70
B_SHARE = 0.90


class AbcClass(StrEnum):
    """ABC class of a product, from its revenue, profit and weeks with sales."""

    A = "A"
    B = "B"
    C = "C"


@dataclass(frozen=True)
class ProductTotals:
    """Sales totals of one product over the window, used to rank it."""

    sku: str
    revenue: Decimal
    profit: Decimal
    weeks_with_sales: int
    last_sale_date: date | None


def recency_factor(last_sale_date: date | None, cutoff: date) -> float:
    """Return 1.0 for a sale in the last 60 days, 0.5 up to 90 days, else 0.0."""
    if last_sale_date is None:
        return 0.0
    days = (cutoff - last_sale_date).days
    if days <= FULL_RECENCY_DAYS:
        return 1.0
    if days <= HALF_RECENCY_DAYS:
        return 0.5
    return 0.0


def class_for_share(cumulative_share: float) -> AbcClass:
    """Return the class for a product's cumulative share of the total score."""
    if cumulative_share <= A_SHARE:
        return AbcClass.A
    if cumulative_share <= B_SHARE:
        return AbcClass.B
    return AbcClass.C


def classify_abc(
    products: Sequence[ProductTotals], cutoff: date
) -> dict[str, AbcClass]:
    """Classify every product against the rest of the collection.

    Products with negative profit are C and are left out of the ranking.
    The product with the highest score is always A. Ties are ranked by sku.
    """
    classes: dict[str, AbcClass] = {}
    ranked: list[ProductTotals] = []
    for product in products:
        if product.profit < 0:
            classes[product.sku] = AbcClass.C
        else:
            ranked.append(product)
    scores = abc_scores(ranked, cutoff)
    total = sum(scores.values())
    if total == 0:
        return classes | {sku: AbcClass.C for sku in scores}

    by_score = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
    cumulative = 0.0
    for position, (sku, score) in enumerate(by_score):
        cumulative += score
        is_top = position == 0
        classes[sku] = AbcClass.A if is_top else class_for_share(cumulative / total)
    return classes


def abc_scores(products: Sequence[ProductTotals], cutoff: date) -> dict[str, float]:
    """Return each product's score, normalized against the collection's maxima.

    score = 0.9 * (0.5 * revenue + 0.3 * profit + 0.2 * weeks) + 0.1 * recency,
    where revenue, profit and weeks are divided by their maximum.
    """
    max_revenue = max((p.revenue for p in products), default=Decimal(0))
    max_profit = max((p.profit for p in products), default=Decimal(0))
    max_weeks = max((p.weeks_with_sales for p in products), default=0)
    return {
        p.sku: BASE_WEIGHT
        * (
            REVENUE_WEIGHT * _ratio(p.revenue, max_revenue)
            + PROFIT_WEIGHT * _ratio(p.profit, max_profit)
            + WEEKS_WEIGHT * _ratio(p.weeks_with_sales, max_weeks)
        )
        + RECENCY_WEIGHT * recency_factor(p.last_sale_date, cutoff)
        for p in products
    }


def _ratio(value: Decimal | int, maximum: Decimal | int) -> float:
    return float(value) / float(maximum) if maximum else 0.0
