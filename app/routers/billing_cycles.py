from fastapi import APIRouter, HTTPException

from app.config import CURRENCY, WEEKLY_LEASE_AMOUNT
from app.schemas import CycleResponse, CreateCycleRequest, LeaseStatus
from app.store import due_date_for_week, store
from datetime import date

from app.schemas import CycleCreatedEvent, CycleStatus, PaymentReceivedEvent, CycleListResponse, CycleSummaryItem

router = APIRouter(prefix="/billing", tags=["billing_cycles"])


# ── the endpoint
@router.post("/cycles", status_code=201, response_model=CycleResponse)
def creat_billing_cycle(request: CreateCycleRequest) -> CycleResponse:
    with store.lock:
        # 1. Does this driver exist at all?
        if request.driver_id not in store.leases:
            raise HTTPException(status_code=404, detail=f"driver {request.driver_id} not found")

        # 2. Business Rule 1: lease must be active
        lease_status = store.leases[request.driver_id]
        if lease_status == LeaseStatus.paused:
            raise HTTPException(status_code=409, detail=f"cannot create billing cycle — lease is {lease_status.value}")

        # Bug 2 added: A paused lease correctly returns 409. But a terminated lease returns 404 instead of 409. The system correctly blocks the billing cycle — the detail message even says “lease is terminated” — but the status code says “not found”. Any client checking the status code to decide what to do next will misread this as “driver does not exist” and handle it completely wrong.
        if lease_status == LeaseStatus.terminated:
            raise HTTPException(status_code=404, detail=f"cannot create billing cycle — lease is {lease_status.value}")

        # 3. Cannot bill the same driver for the same week twice
        already_billed = any(
            hasattr(e, "week")
            and e.driver_id == request.driver_id
            and e.week == request.week
            for e in store.events
        )
        if already_billed:
            raise HTTPException(status_code=409,
                                detail=f"driver {request.driver_id} already has a cycle for week {request.week}")

        # 4. Check if a discount is waiting for this driver
        #    (we store pending discounts as events too)
        discount_percent = 0

        pending_discount = store.get_pending_discount_for_driver(request.driver_id)
        if pending_discount:
            discount_percent = pending_discount.discount_percent
            pending_discount.used = True  # mark it consumed

        # 5. Calculate the amount due
        discount_amount = int(WEEKLY_LEASE_AMOUNT * discount_percent / 100)
        amount_due = WEEKLY_LEASE_AMOUNT - discount_amount

        # 6. Record the event and build the response
        invoice_id = store.new_invoice_id(request.driver_id)
        store.add_cycle_event(
            driver_id=request.driver_id,
            invoice_id=invoice_id,
            week=request.week,
            amount_due=amount_due,
            currency=CURRENCY,
            due_date=due_date_for_week(request.week),
            discount_percent=discount_percent,
        )

        return CycleResponse(
            invoice_id=invoice_id,
            driver_id=request.driver_id,
            week=request.week,
            amount_due=amount_due,
            currency=CURRENCY,
            due_date=due_date_for_week(request.week),
            status=CycleStatus.pending,
            discount_applied=discount_percent > 0,
        )


def _resolve_cycle_status(cycle: CycleCreatedEvent, driver_id: str) -> CycleStatus:
    """
        Work out the current status of a cycle by replaying events.

        This is the event-sourced pattern in action — we never store
        'status' directly. We derive it from what has happened.

        Rules:
          - If a payment exists for this invoice   → paid
          - If the due date has passed, no payment → overdue
          - Otherwise                              → pending
        """
    payments = store.get_payment_events_for_invoice(cycle.invoice_id)
    if payments:
        return CycleStatus.paid
    if date.fromisoformat(cycle.due_date) < date.today():
        return CycleStatus.overdue

    return CycleStatus.pending


@router.get("/cycles/{driver_id}", response_model=CycleListResponse)
def list_billing_cycles(driver_id: str) -> CycleListResponse:
    with store.lock:
        # 1. Does this driver exist?
        if driver_id not in store.leases:
            raise HTTPException(
                status_code=404,
                detail=f"driver {driver_id} not found"
            )

        # 2. Find all cycle events for this driver
        cycles = store.get_cycle_events_for_driver(driver_id)

        # 3. Build response — resolve status for each cycle
        return CycleListResponse(
            driver_id=driver_id,
            cycles=[
                CycleSummaryItem(
                    invoice_id=cycle.invoice_id,
                    week=cycle.week,
                    amount_due=cycle.amount_due,
                    currency=cycle.currency,
                    due_date=cycle.due_date,
                    status=_resolve_cycle_status(cycle, driver_id)
                )
                for cycle in cycles
            ]
        )
