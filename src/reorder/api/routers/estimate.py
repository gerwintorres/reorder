from fastapi import APIRouter, status

from reorder.domain.demand import estimate_demand
from reorder.schemas.errors import ErrorsOut
from reorder.schemas.estimate import EstimatePreviewIn, EstimatePreviewOut

router = APIRouter(
    tags=["estimate"],
    responses={status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": ErrorsOut}},
)


@router.post("/estimate/preview")
def preview_estimate(payload: EstimatePreviewIn) -> EstimatePreviewOut:
    """Estimate the weekly demand of one product from the sales in the request."""
    estimate = estimate_demand(
        payload.to_history(), payload.abc, payload.rotation, payload.cutoff_date
    )
    return EstimatePreviewOut.from_estimate(payload.sku, estimate)
