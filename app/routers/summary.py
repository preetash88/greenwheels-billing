from datetime import date

from fastapi import APIRouter, HTTPException

from app.config import OVERDUE_THRESHOLD
from app.schemas import SummaryResponse, AccountStatus
from app.store import store

router = APIRouter(prefix="/billing", tags=["summary"])


@router.get("/summary/{driver_id}", response_model=SummaryResponse)
def get_summary(driver_id: str) -> SummaryResponse:
    with store.lock:
        # 1. Does this driver exist?
        if driver_id not in store.leases:
            raise HTTPException(
                status_code=404,
                detail=f"driver {driver_id} not found"
            )

        # 2. Get all cycle events for this driver
        cycles = store.get_cycle_events_for_driver(driver_id)

        # 3. Get all payment events for this driver
        payments = store.get_payment_events_for_driver(driver_id)

        # 4. Build a set of paid invoice IDs for quick lookup
        paid_invoice_ids = {p.invoice_id for p in payments}

        # 5. Calculate totals
        total_billed = sum(c.amount_due for c in cycles)
        total_paid = sum(p.amount for p in payments)
        total_outstanding = max(0, total_billed - total_paid)

        # 6. Business Rule 3 — count CONSECUTIVE missed payments
        #
        # A missed payment = a cycle whose due date has passed and no payment was recorded for it.
        #
        # We sort cycles by week and count how many consecutive ones at the END of the list are unpaid and overdue.
        # The streak resets the moment we find a paid cycle.
        #
        # Example:
        #   week 1 → paid      ← streak resets here
        #   week 2 → overdue   ← streak = 1
        #   week 3 → overdue   ← streak = 2
        #   week 4 → overdue   ← streak = 3 → flagged overdue
        #
        sorted_cycles = sorted(cycles, key=lambda c: c.week)
        consecutive_missed = 0

        for cycle in reversed(sorted_cycles):
            is_paid = cycle.invoice_id in paid_invoice_ids
            is_overdue = date.fromisoformat(cycle.due_date) < date.today()

            if not is_paid and is_overdue:
                consecutive_missed += 1
            else:
                break  # streak broken — stop counting

        # 7. Determine account status
        account_status = AccountStatus.overdue if consecutive_missed >= OVERDUE_THRESHOLD else AccountStatus.ok

        return SummaryResponse(
            driver_id=driver_id,
            total_billed=total_billed,
            total_paid=total_paid,
            total_outstanding=total_outstanding,
            missed_payment_count=consecutive_missed,
            status=account_status,
        )
