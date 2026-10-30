from dataclasses import asdict
from datetime import date

from pydantic import BaseModel, ConfigDict, Field, JsonValue

from reorder.domain.classification import AbcClass
from reorder.domain.demand import DemandEstimate, Rule
from reorder.domain.rotation import Rotation
from reorder.domain.series import ProductHistory, WeeklyPoint

# 13 weeks with three spikes (40, 52, 104); estimates a demand of 37.
PREVIEW_EXAMPLE: dict[str, JsonValue] = {
    "sku": "A-100",
    "points": [
        {"week_start": "2026-03-30", "qty": 4},
        {"week_start": "2026-04-06", "qty": 4},
        {"week_start": "2026-04-13", "qty": 4},
        {"week_start": "2026-04-20", "qty": 12},
        {"week_start": "2026-04-27", "qty": 12},
        {"week_start": "2026-05-04", "qty": 12},
        {"week_start": "2026-05-11", "qty": 16},
        {"week_start": "2026-05-18", "qty": 20},
        {"week_start": "2026-05-25", "qty": 20},
        {"week_start": "2026-06-01", "qty": 24},
        {"week_start": "2026-06-08", "qty": 40},
        {"week_start": "2026-06-15", "qty": 52},
        {"week_start": "2026-06-22", "qty": 104},
    ],
    "abc": "A",
    "rotation": "medium",
    "last_sale_date": "2026-06-24",
    "cutoff_date": "2026-06-29",
}


class WeeklyPointIn(BaseModel):
    week_start: date
    qty: int = Field(ge=0, strict=True)


class EstimatePreviewIn(BaseModel):
    model_config = ConfigDict(json_schema_extra={"examples": [PREVIEW_EXAMPLE]})

    sku: str = Field(min_length=1)
    points: list[WeeklyPointIn]
    abc: AbcClass
    rotation: Rotation
    last_sale_date: date | None = None
    last_purchase_date: date | None = None
    cutoff_date: date

    def to_history(self) -> ProductHistory:
        """Build the domain history from the request."""
        return ProductHistory(
            sku=self.sku,
            points=tuple(
                WeeklyPoint(week_start=p.week_start, qty=p.qty) for p in self.points
            ),
            last_sale_date=self.last_sale_date,
            last_purchase_date=self.last_purchase_date,
        )


class EstimatePreviewOut(BaseModel):
    sku: str
    demand: int
    rule: Rule
    reason: str
    avg: float
    std: float
    k: float
    base_demand: int
    efficiency: float
    q1: float | None
    q3: float | None
    ceiling: float | None
    excluded: list[int]

    @classmethod
    def from_estimate(cls, sku: str, estimate: DemandEstimate) -> "EstimatePreviewOut":
        """Build the response from a domain estimate."""
        return cls(sku=sku, **asdict(estimate))
