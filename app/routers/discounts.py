from fastapi import APIRouter, HTTPException

from app.config import MAX_PENDING_DISCOUNTS
from app.schemas import DiscountResponse, CreateDiscountRequest, LeaseStatus
from app.store import store

router = APIRouter(prefix="/billing", tags=["discounts"])


@router.post("/discounts", response_model=DiscountResponse, status_code=201)
def apply_discount(request: CreateDiscountRequest) -> DiscountResponse:
    with store.lock:
        # 1. Does this driver exist?
        if request.driver_id not in store.leases:
            raise HTTPException(
                status_code=404,
                detail=f"driver {request.driver_id} not found"
            )

        # 2. Lease must be active to receive a discount
        lease_status = store.leases[request.driver_id]
        if lease_status != LeaseStatus.active:
            raise HTTPException(
                status_code=422,
                detail=(
                    f"driver {request.driver_id} is not eligible for a discount — "
                    f"lease is {lease_status.value}"
                )
            )

        # 3. Business Rule 4 — discounts do not stack
        #    If a discount is already pending for this driver, reject a second one
        pending_count = store.count_pending_discounts_for_driver(request.driver_id)
        if pending_count >= MAX_PENDING_DISCOUNTS:
            raise HTTPException(
                status_code=422,
                detail=(
                    f"driver {request.driver_id} already has a pending discount — "
                    f"discounts do not stack"
                )
            )

        #  4. Record the discount event
        store.add_discount_event(
            driver_id=request.driver_id,
            discount_percent=request.discount_percent,
            used=False,
        )

        return DiscountResponse(
            driver_id=request.driver_id,
            discount_percent=request.discount_percent,
            applies_to_next_cycle=True,
            message=(
                f"{request.discount_percent}% discount will apply to "
                f"{request.driver_id}'s next billing cycle"
            )
        )
