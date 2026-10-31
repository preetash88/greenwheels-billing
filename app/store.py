from typing import Union

from app.config import BILLING_START_DATE, WEEKLY_LEASE_AMOUNT, CURRENCY
import threading
from datetime import timedelta

from app.schemas import CycleCreatedEvent, PaymentReceivedEvent, DiscountAppliedEvent, LeaseStatus, InvoiceCounter

# type alias — an event is one of these three types
Event = Union[CycleCreatedEvent, PaymentReceivedEvent, DiscountAppliedEvent]


def due_date_for_week(week: int) -> str:
    """Week 1 is due 7 days after the billing start date, week 2 after 14 days, etc."""
    return (BILLING_START_DATE + timedelta(days=7 * week)).isoformat()


class Store:
    """
    The stub's in-memory database.

    leases  — maps driver_id to LeaseStatus
    events  — append-only list of typed event objects
    counter — generates unique sequential invoice IDs
    lock    — ensures only one request modifies data at a time
    """

    def __init__(self):
        # Many requests can arrive at the same time, so we use a lock
        # to make sure only one request changes the data at a time.
        self.lock = threading.Lock()
        self.leases: dict[str, LeaseStatus] = {}
        self.events: list[Event] = []
        self.counter: InvoiceCounter = InvoiceCounter()
        self.reset()

    def reset(self):
        """Wipe everything and reload seed data. The caller must hold the lock."""
        self.leases = {}
        self.events = []
        self.counter = InvoiceCounter()
        self._load_seed_data()

    # ---------- small helpers ----------
    def new_invoice_id(self, driver_id: str) -> str:
        return self.counter.generate(driver_id)

    def add_cycle_event(self, **data) -> CycleCreatedEvent:
        event = CycleCreatedEvent(
            event_id=len(self.events) + 1,
            **data
        )
        self.events.append(event)
        return event

    def add_payment_event(self, **data) -> PaymentReceivedEvent:
        event = PaymentReceivedEvent(
            event_id=len(self.events) + 1,
            **data
        )
        self.events.append(event)
        return event

    def add_discount_event(self, **data) -> DiscountAppliedEvent:
        event = DiscountAppliedEvent(
            event_id=len(self.events) + 1,
            **data
        )
        self.events.append(event)
        return event

    # ---------- seed data ----------
    def _load_seed_data(self):
        # Lease status for each driver
        self.leases = {
            "DRIVER-001": LeaseStatus.active,  # main driver, has billing history
            "DRIVER-002": LeaseStatus.paused,  # used to test: cannot bill a paused lease
            "DRIVER-003": LeaseStatus.terminated,  # used to test: cannot bill a terminated lease
            "DRIVER-004": LeaseStatus.active,  # clean driver, no history, used for overdue/discount tests
        }

        # DRIVER-001 already has two weeks of billing history, both paid
        for week in (1, 2):
            invoice_id = self.new_invoice_id("DRIVER-001")
            self.add_cycle_event(
                driver_id=f"DRIVER-001",
                invoice_id=invoice_id,
                week=week,
                amount_due=WEEKLY_LEASE_AMOUNT,
                currency=CURRENCY,
                due_date=due_date_for_week(week),
                discount_percent=0
            )

            self.add_payment_event(
                driver_id="DRIVER-001",
                invoice_id=invoice_id,
                payment_reference=f"SEED-PAY-W{week}",
                amount=WEEKLY_LEASE_AMOUNT,
                currency=CURRENCY
            )

    def get_payment_events_for_invoice(self, invoice_id: str) -> list:
        """Returns all payment events for a given invoice ID."""
        return [
            e for e in self.events
            if hasattr(e, "invoice_id") and hasattr(e, "payment_reference") and e.invoice_id == invoice_id
        ]

    def get_cycle_events_for_driver(self, driver_id: str) -> list:
        """Returns all cycle created events for a given driver."""
        return [
            e for e in self.events
            if hasattr(e, "week")
               and hasattr(e, "invoice_id")
               and e.driver_id == driver_id
        ]

    def get_payment_events_for_driver(self, driver_id: str) -> list:
        """Returns all payment events for a given driver."""
        return [
            e for e in self.events
            if hasattr(e, "payment_reference")
               and e.driver_id == driver_id
        ]

    def find_cycle_by_invoice_id(self, invoice_id: str):
        """Returns the cycle event for a given invoice ID, or None."""
        return next(
            (
                e for e in self.events
                if hasattr(e, "week")
                   and hasattr(e, "invoice_id")
                   and e.invoice_id == invoice_id
            ),
            None,
        )

    def find_payment_by_reference(self, payment_reference: str):
        """Returns a payment event matching the reference, or None."""
        return next(
            (
                e for e in self.events
                if hasattr(e, "payment_reference")
                   and e.payment_reference == payment_reference
            ),
            None,
        )

    def get_pending_discount_for_driver(self, driver_id: str):
        """Returns the first unused discount event for a driver, or None."""
        return next(
            (
                e for e in reversed(self.events)
                if hasattr(e, "discount_percent")
                   and hasattr(e, "used")
                   and e.driver_id == driver_id
                   and not e.used
            ),
            None,
        )

    def count_pending_discounts_for_driver(self, driver_id: str) -> int:
        """Counts unused discount events for a driver."""
        return sum(
            1 for e in self.events
            if hasattr(e, "discount_percent")
            and hasattr(e, "used")
            and e.driver_id == driver_id
            and not e.used
        )


# One shared store for the whole app
store = Store()
