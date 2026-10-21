import pytest

from reorder.domain.peaks import (
    ceiling,
    filtered_std,
    min_count,
    quartiles,
    repeated_value,
    split_peaks,
)

# 13 weeks with sales, three of them spikes.
GOLDEN = [4, 4, 4, 12, 12, 12, 16, 20, 20, 24, 40, 52, 104]


def test_quartiles_interpolate_between_neighbours() -> None:
    # The default method is "exclusive", which gives (1.25, 3.75) here.
    assert quartiles([1, 2, 3, 4]) == pytest.approx((1.75, 3.25))


def test_quartiles_of_golden_case() -> None:
    assert quartiles(GOLDEN) == pytest.approx((12, 24))


def test_min_count_is_at_least_two() -> None:
    assert min_count(len(GOLDEN)) == 2


def test_repeated_value_is_highest_value_seen_min_count_times() -> None:
    assert repeated_value(GOLDEN, threshold=2) == 20


def test_ceiling_of_golden_case_is_q3_plus_iqr() -> None:
    assert ceiling(GOLDEN) == pytest.approx(36)


def test_split_peaks_excludes_single_values_at_or_above_ceiling() -> None:
    _, excluded = split_peaks(GOLDEN)
    assert excluded == [40, 52, 104]


def test_split_peaks_keeps_the_rest_in_order() -> None:
    kept, _ = split_peaks(GOLDEN)
    assert kept == [4, 4, 4, 12, 12, 12, 16, 20, 20, 24]


def test_filtered_std_of_golden_case_is_sample_std_of_kept_values() -> None:
    # pstdev (divides by n) would give 6.88.
    assert filtered_std(GOLDEN) == pytest.approx(7.254, abs=0.005)
