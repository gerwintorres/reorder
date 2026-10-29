from fastapi import APIRouter

from reorder.domain.demand import estimate_demand
from reorder.schemas.estimate import EstimatePreviewIn, EstimatePreviewOut

router = APIRouter(tags=["estimate"])


@router.post("/estimate/preview")
def preview_estimate(payload: EstimatePreviewIn) -> EstimatePreviewOut:
    """Estimate the weekly demand of one product from the sales in the request."""
    estimate = estimate_demand(
        payload.to_history(), payload.abc, payload.rotation, payload.cutoff_date
    )
    return EstimatePreviewOut.from_estimate(payload.sku, estimate)
