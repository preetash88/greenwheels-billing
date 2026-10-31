from fastapi import APIRouter, Response, HTTPException

from app.config import CURRENCY
from app.schemas import CreatePaymentRequest, PaymentResponse
from app.store import store

router = APIRouter(prefix="/billing", tags=["payments"])


@router.post("/payments", response_model=PaymentResponse, status_code=201)
def record_payment(request: CreatePaymentRequest, response: Response) -> PaymentResponse:
    with store.lock:
        # 1. Does this invoice exist?
        #    We find it by scanning cycle events — event sourcing pattern
        cycle_event = store.find_cycle_by_invoice_id(request.invoice_id)
        if cycle_event is None:
            raise HTTPException(
                status_code=404,
                detail=f"invoice {request.invoice_id} not found"
            )

        # 2. Business Rule 2 — idempotency check
        #    Scan payment events for this exact payment reference
        #    If found, return 200 with "duplicate" status — nothing new created
        existing_payment = store.find_payment_by_reference(request.payment_reference)
        if existing_payment is not None:
            response.status_code = 200
            return PaymentResponse(
                payment_reference=existing_payment.payment_reference,
                invoice_id=existing_payment.invoice_id,
                amount=existing_payment.amount,
                currency=existing_payment.currency,
                status="duplicate",
                message=(
                    f"payment {request.payment_reference} was already recorded — "
                    f"no duplicate credit applied"
                )
            )

        new_payment = store.add_payment_event(
            driver_id=cycle_event.driver_id,
            invoice_id=request.invoice_id,
            payment_reference=request.payment_reference,
            amount=request.amount,
            currency=CURRENCY,
        )

        return PaymentResponse(
            payment_reference=new_payment.payment_reference,
            invoice_id=new_payment.invoice_id,
            amount=new_payment.amount,
            currency=new_payment.currency,
            status="recorded",
            message=f"payment {request.payment_reference} recorded successfully",
        )
