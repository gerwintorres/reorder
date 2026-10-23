from calendar import MONDAY
from dataclasses import dataclass
from datetime import date, timedelta

DEFAULT_WINDOW_WEEKS = 52


@dataclass(frozen=True)
class WeeklyPoint:
    """Units sold in one week, keyed by the Monday that starts it.

    Raises:
        ValueError: If week_start is not a Monday, or qty is negative or a bool.
    """

    week_start: date
    qty: int

    def __post_init__(self) -> None:
        if self.week_start.weekday() != MONDAY:
            raise ValueError(f"week_start must be a Monday, got {self.week_start!r}")
        if isinstance(self.qty, bool) or self.qty < 0:
            raise ValueError(f"qty must be a non-negative integer, got {self.qty!r}")


@dataclass(frozen=True)
class ProductHistory:
    """Weekly sales of one product plus the dates the recency rules need.

    Raises:
        ValueError: If sku is blank.
    """

    sku: str
    points: tuple[WeeklyPoint, ...]
    last_sale_date: date | None
    last_purchase_date: date | None

    def __post_init__(self) -> None:
        if not self.sku.strip():
            raise ValueError(f"sku must not be blank, got {self.sku!r}")


def weeks_with_sales(
    history: ProductHistory, cutoff: date, window_weeks: int = DEFAULT_WINDOW_WEEKS
) -> list[WeeklyPoint]:
    """Return the weeks with sales in the window before cutoff, oldest first.

    The window starts window_weeks weeks before cutoff. A week starting on
    cutoff or later is outside it, and weeks with qty 0 don't count.
    """
    start = cutoff - timedelta(weeks=window_weeks)
    return sorted(
        (
            point
            for point in history.points
            if start <= point.week_start < cutoff and point.qty > 0
        ),
        key=lambda point: point.week_start,
    )
