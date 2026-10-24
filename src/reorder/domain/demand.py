import math
import statistics
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, timedelta
from enum import StrEnum

from reorder.domain.classification import AbcClass
from reorder.domain.peaks import (
    MIN_VALUES_TO_FILTER,
    ceiling,
    filtered_std,
    quartiles,
    split_peaks,
)
from reorder.domain.rotation import Rotation
from reorder.domain.series import ProductHistory, WeeklyPoint, weeks_with_sales
from reorder.domain.service_level import k_for

RECENT_SALE_WEEKS = 3
RECENT_SALE_DAYS = 60
STALE_SALE_DAYS = 90
STALE_PURCHASE_DAYS = 90
RECENT_AVERAGE_WEEKS = 8


class Rule(StrEnum):
    """Rule that set the demand, in the order the rules are checked."""

    NO_SALES = "no_sales"
    SINGLE_STALE_SALE = "single_stale_sale"
    MISSING_LAST_SALE_DATE = "missing_last_sale_date"
    STALE_LAST_SALE = "stale_last_sale"
    RECENT_AVERAGE_CAP = "recent_average_cap"
    STATISTICAL_BASE = "statistical_base"


@dataclass(frozen=True)
class DemandEstimate:
    """Weekly demand of one product, the rule that set it and how it was computed.

    q1, q3 and ceiling are None when the series was too short to filter peaks.
    """

    demand: int
    rule: Rule
    reason: str
    avg: float
    std: float
    k: float
    base_demand: int
    efficiency: float
    q1: float | None
    q3: float | None
    ceiling: float | None
    excluded: tuple[int, ...]


def average(qtys: Sequence[int]) -> float:
    """Return the mean of the quantities, or 0.0 when there are none."""
    return statistics.fmean(qtys) if qtys else 0.0


def base_demand(avg: float, k: float, std: float) -> int:
    """Return the demand before recency rules: avg + k * std, rounded up."""
    return math.ceil(avg + k * std)


def efficiency(qtys: Sequence[int], demand: int) -> float:
    """Return the share of weeks with sales that the demand would have covered.

    It is measured on the same weeks the demand was estimated from, so it
    describes the history, not how well the demand will cover future weeks.
    Returns 0.0 when there are no weeks.
    """
    if not qtys:
        return 0.0
    covered = sum(1 for qty in qtys if qty <= demand)
    return covered / len(qtys)


def estimate_demand(
    history: ProductHistory, abc: AbcClass, rotation: Rotation, cutoff: date
) -> DemandEstimate:
    """Estimate the weekly demand of one product at the cutoff date."""
    weeks = weeks_with_sales(history, cutoff)
    qtys = [week.qty for week in weeks]
    avg = average(qtys)
    std = filtered_std(qtys)
    k = k_for(abc, rotation)
    base = base_demand(avg, k, std)
    base_reason = f"Average {avg:.2f}, k {k:.2f}, std {std:.2f}."
    rule, demand, reason = _apply_rules(history, weeks, cutoff, base, base_reason)

    filtered = len(qtys) >= MIN_VALUES_TO_FILTER
    q1, q3 = quartiles(qtys) if filtered else (None, None)
    _, excluded = split_peaks(qtys)
    return DemandEstimate(
        demand=demand,
        rule=rule,
        reason=reason,
        avg=avg,
        std=std,
        k=k,
        base_demand=base,
        efficiency=efficiency(qtys, demand),
        q1=q1,
        q3=q3,
        ceiling=ceiling(qtys) if filtered else None,
        excluded=tuple(excluded),
    )


def _apply_rules(
    history: ProductHistory,
    weeks: Sequence[WeeklyPoint],
    cutoff: date,
    base: int,
    base_reason: str,
) -> tuple[Rule, int, str]:
    """Return the first rule that applies, with its demand and reason."""
    if not weeks:
        return Rule.NO_SALES, 0, "No sales in history."
    recent_start = cutoff - timedelta(weeks=RECENT_SALE_WEEKS)
    if len(weeks) == 1 and weeks[0].week_start < recent_start:
        reason = f"Single sale older than {RECENT_SALE_WEEKS} weeks."
        return Rule.SINGLE_STALE_SALE, 0, reason
    if history.last_sale_date is None:
        return Rule.MISSING_LAST_SALE_DATE, 0, "Missing last sale date."

    days_since_sale = (cutoff - history.last_sale_date).days
    if days_since_sale > STALE_SALE_DAYS:
        return Rule.STALE_LAST_SALE, 0, f"Last sale {days_since_sale} days ago."
    stale_purchase = (
        history.last_purchase_date is not None
        and (cutoff - history.last_purchase_date).days > STALE_PURCHASE_DAYS
    )
    if days_since_sale > RECENT_SALE_DAYS or stale_purchase:
        recent = weeks[-RECENT_AVERAGE_WEEKS:]
        recent_demand = math.ceil(average([week.qty for week in recent]))
        reason = "Stale sale or purchase; capped at recent average."
        return Rule.RECENT_AVERAGE_CAP, min(base, recent_demand), reason
    return Rule.STATISTICAL_BASE, base, base_reason
