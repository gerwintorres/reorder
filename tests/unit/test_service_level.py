from itertools import product

import pytest

from reorder.domain.classification import AbcClass
from reorder.domain.rotation import Rotation
from reorder.domain.service_level import SERVICE_LEVEL_TARGETS, k_for


@pytest.mark.parametrize(
    ("abc", "rotation", "expected"),
    [
        (AbcClass.A, Rotation.HIGH, 1.88),
        (AbcClass.A, Rotation.MEDIUM, 1.64),
        (AbcClass.A, Rotation.LOW, 0.25),
        (AbcClass.B, Rotation.HIGH, 1.64),
        (AbcClass.B, Rotation.MEDIUM, 1.28),
        (AbcClass.B, Rotation.LOW, 0.13),
        (AbcClass.C, Rotation.HIGH, 1.04),
        (AbcClass.C, Rotation.MEDIUM, 0.84),
        (AbcClass.C, Rotation.LOW, 0.13),
    ],
)
def test_k_for_matches_spec_table(
    abc: AbcClass, rotation: Rotation, expected: float
) -> None:
    # Exact comparison: k_for rounds to two decimals.
    assert k_for(abc, rotation) == expected


def test_every_class_and_rotation_has_a_target() -> None:
    assert set(SERVICE_LEVEL_TARGETS) == set(product(AbcClass, Rotation))


def test_every_target_is_a_valid_probability() -> None:
    # inv_cdf only accepts 0 < p < 1.
    assert all(0 < target < 1 for target in SERVICE_LEVEL_TARGETS.values())
