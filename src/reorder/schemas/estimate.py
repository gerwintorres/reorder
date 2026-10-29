from dataclasses import asdict
from datetime import date

from pydantic import BaseModel, Field

from reorder.domain.classification import AbcClass
from reorder.domain.demand import DemandEstimate, Rule
from reorder.domain.rotation import Rotation
from reorder.domain.series import ProductHistory, WeeklyPoint


class WeeklyPointIn(BaseModel):
    week_start: date
    qty: int = Field(ge=0, strict=True)


class EstimatePreviewIn(BaseModel):
    sku: str = Field(min_length=1)
    points: list[WeeklyPointIn]
    abc: AbcClass
    rotation: Rotation
    last_sale_date: date | None
    last_purchase_date: date | None
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
