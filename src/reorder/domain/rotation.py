from enum import StrEnum

from reorder.domain.series import DEFAULT_WINDOW_WEEKS

HIGH_ROTATION_SHARE = 0.60
LOW_ROTATION_SHARE = 0.25


class Rotation(StrEnum):
    """How often a product sells, from its share of weeks with sales."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


def rotation_for(
    weeks_with_sales: int, window_weeks: int = DEFAULT_WINDOW_WEEKS
) -> Rotation:
    """Return high from 60 % of weeks with sales, low up to 25 %, else medium."""
    share = weeks_with_sales / window_weeks
    if share >= HIGH_ROTATION_SHARE:
        return Rotation.HIGH
    if share <= LOW_ROTATION_SHARE:
        return Rotation.LOW
    return Rotation.MEDIUM
