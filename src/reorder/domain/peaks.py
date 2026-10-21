import math
import statistics
from collections import Counter
from collections.abc import Sequence

MIN_REPEATS = 2
REPEAT_SHARE = 0.05


def quartiles(values: Sequence[int]) -> tuple[float, float]:
    """Return Q1 and Q3 with linear interpolation, as NumPy and pandas do."""
    q1, _, q3 = statistics.quantiles(values, n=4, method="inclusive")
    return q1, q3


def min_count(n: int) -> int:
    """Return how many times a value must appear to count as real demand."""
    return max(MIN_REPEATS, math.ceil(n * REPEAT_SHARE))


def repeated_value(values: Sequence[int], threshold: int) -> int:
    """Return the highest value that appears at least `threshold` times, or 0."""
    counts = Counter(values)
    return max(
        (value for value, count in counts.items() if count >= threshold), default=0
    )


def ceiling(values: Sequence[int]) -> float:
    """Return Q3 + IQR, raised to the highest repeated value if that is higher."""
    q1, q3 = quartiles(values)
    return max(q3 + (q3 - q1), repeated_value(values, min_count(len(values))))


def split_peaks(values: Sequence[int]) -> tuple[list[int], list[int]]:
    """Split values into (kept, excluded); a peak is both high and rare."""
    top = ceiling(values)
    threshold = min_count(len(values))
    counts = Counter(values)
    kept: list[int] = []
    excluded: list[int] = []
    for value in values:
        if value >= top and counts[value] < threshold:
            excluded.append(value)
        else:
            kept.append(value)
    return kept, excluded


def filtered_std(values: Sequence[int]) -> float:
    """Return the sample standard deviation of the values left after split_peaks."""
    kept, _ = split_peaks(values)
    return statistics.stdev(kept)
