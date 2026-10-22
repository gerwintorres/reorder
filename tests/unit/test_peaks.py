from statistics import StatisticsError

import pytest

from reorder.domain import peaks
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


def test_quartiles_need_at_least_two_values() -> None:
    with pytest.raises(StatisticsError):
        quartiles([5])


@pytest.mark.parametrize(
    ("n", "expected"),
    [(4, 2), (13, 2), (40, 2), (41, 3), (52, 3)],
)
def test_min_count_is_two_until_five_percent_of_n_exceeds_it(
    n: int, expected: int
) -> None:
    assert min_count(n) == expected


def test_repeated_value_is_highest_value_seen_min_count_times() -> None:
    assert repeated_value(GOLDEN, threshold=2) == 20


def test_repeated_value_is_zero_when_nothing_repeats() -> None:
    assert repeated_value([1, 2, 3], threshold=2) == 0


def test_ceiling_of_golden_case_is_q3_plus_iqr() -> None:
    assert ceiling(GOLDEN) == pytest.approx(36)


def test_ceiling_rises_to_repeated_value_when_higher_than_iqr() -> None:
    # Q3 + IQR is 36, but 60 repeats, so it is demand, not a spike.
    assert ceiling([4, 4, 4, 12, 12, 12, 16, 20, 20, 24, 50, 60, 60]) == 60


def test_split_peaks_excludes_single_values_at_or_above_ceiling() -> None:
    _, excluded = split_peaks(GOLDEN)
    assert excluded == [40, 52, 104]


def test_split_peaks_keeps_the_rest_in_order() -> None:
    kept, _ = split_peaks(GOLDEN)
    assert kept == [4, 4, 4, 12, 12, 12, 16, 20, 20, 24]


def test_split_peaks_excludes_single_value_equal_to_ceiling() -> None:
    _, excluded = split_peaks([4, 4, 4, 12, 12, 12, 16, 20, 20, 24, 36, 52, 104])
    assert excluded == [36, 52, 104]


def test_split_peaks_keeps_high_value_repeated_min_count_times() -> None:
    _, excluded = split_peaks([*GOLDEN, 104])
    assert excluded == []


def test_split_peaks_excludes_high_value_repeated_fewer_than_min_count_times() -> None:
    # n = 41, so min_count is 3 and appearing twice is not enough.
    _, excluded = split_peaks([10] * 20 + [20] * 19 + [500, 500])
    assert excluded == [500, 500]


def test_split_peaks_does_not_filter_fewer_than_four_values() -> None:
    assert split_peaks([1, 1, 100]) == ([1, 1, 100], [])


def test_split_peaks_filters_from_four_values() -> None:
    assert split_peaks([10, 10, 12, 50]) == ([10, 10, 12], [50])


def test_split_peaks_keeps_everything_when_filter_would_leave_fewer_than_three(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # With the current rules the filter never leaves fewer than three values,
    # so the guard is reached by forcing a ceiling below every value.
    # Only the repeated 1s survive the filter: two values, one under the limit.
    monkeypatch.setattr(peaks, "ceiling", lambda values: 0.0)
    assert split_peaks([1, 1, 2, 3]) == ([1, 1, 2, 3], [])


def test_filtered_std_of_golden_case_is_sample_std_of_kept_values() -> None:
    # pstdev (divides by n) would give 6.88.
    assert filtered_std(GOLDEN) == pytest.approx(7.254, abs=0.005)


def test_filtered_std_of_fewer_than_four_values_uses_all_of_them() -> None:
    assert filtered_std([2, 4, 9]) == pytest.approx(3.606, abs=0.005)


def test_filtered_std_of_two_values() -> None:
    assert filtered_std([4, 8]) == pytest.approx(2.828, abs=0.005)


@pytest.mark.parametrize("values", [[], [7]])
def test_filtered_std_is_zero_below_two_values(values: list[int]) -> None:
    assert filtered_std(values) == 0.0
