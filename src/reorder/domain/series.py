from calendar import MONDAY
from dataclasses import dataclass
from datetime import date


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


def positive_qtys(history: ProductHistory) -> list[int]:
    """Return the quantities of the weeks with sales; zero weeks don't count."""
    return [point.qty for point in history.points if point.qty > 0]
