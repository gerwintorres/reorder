from enum import StrEnum


class Rotation(StrEnum):
    """How often a product sells, from its share of weeks with sales."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
