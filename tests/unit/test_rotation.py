import pytest

from reorder.domain.rotation import Rotation, rotation_for


@pytest.mark.parametrize(
    ("weeks_with_sales", "expected"),
    [(12, Rotation.HIGH), (5, Rotation.LOW), (8, Rotation.MEDIUM)],
)
def test_rotation_at_60_25_and_40_percent(
    weeks_with_sales: int, expected: Rotation
) -> None:
    # Over 20 weeks: 12 is 0.60, 5 is 0.25, 8 is 0.40.
    assert rotation_for(weeks_with_sales, window_weeks=20) is expected


@pytest.mark.parametrize(
    ("weeks_with_sales", "expected"),
    [
        (32, Rotation.HIGH),
        (31, Rotation.MEDIUM),
        (14, Rotation.MEDIUM),
        (13, Rotation.LOW),
        (0, Rotation.LOW),
        (52, Rotation.HIGH),
    ],
)
def test_rotation_over_default_52_week_window(
    weeks_with_sales: int, expected: Rotation
) -> None:
    assert rotation_for(weeks_with_sales) is expected
