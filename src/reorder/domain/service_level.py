from statistics import NormalDist

from reorder.domain.classification import AbcClass
from reorder.domain.rotation import Rotation

SERVICE_LEVEL_TARGETS: dict[tuple[AbcClass, Rotation], float] = {
    (AbcClass.A, Rotation.HIGH): 0.97,
    (AbcClass.A, Rotation.MEDIUM): 0.95,
    (AbcClass.A, Rotation.LOW): 0.60,
    (AbcClass.B, Rotation.HIGH): 0.95,
    (AbcClass.B, Rotation.MEDIUM): 0.90,
    (AbcClass.B, Rotation.LOW): 0.55,
    (AbcClass.C, Rotation.HIGH): 0.85,
    (AbcClass.C, Rotation.MEDIUM): 0.80,
    (AbcClass.C, Rotation.LOW): 0.55,
}


def k_for(abc: AbcClass, rotation: Rotation) -> float:
    """Return the safety factor k for a class and rotation, rounded to two decimals.

    k is derived from the target service level with the inverse normal CDF,
    so there is no hand-written table of k values to get wrong.
    """
    return round(NormalDist().inv_cdf(SERVICE_LEVEL_TARGETS[abc, rotation]), 2)
