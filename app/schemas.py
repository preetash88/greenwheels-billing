from enum import Enum

from pydantic import BaseModel, field_validator

from app.config import CURRENCY


# ─────────────────────────────────────────────
#  ENUMS — fixed allowed values
# ─────────────────────────────────────────────
class LeaseStatus(str, Enum):
    active = "active"
    paused = "paused"
    terminated = "terminated"


class CycleStatus(str, Enum):
    pending = "pending"
    paid = "paid"
    overdue = "overdue"
    disputed = "disputed"


class EventType(str, Enum):
    cycle_created = "CYCLE_CREATED"
    payment_received = "PAYMENT_RECEIVED"
    discount_applied = "DISCOUNT_APPLIED"


class AccountStatus(str, Enum):
    ok = "ok"
    overdue = "overdue"


# ─────────────────────────────────────────────
#  INTERNAL STORE MODELS
#  These define the shape of data INSIDE the store.
#  They are never returned directly to the API caller.
# ─────────────────────────────────────────────
class CycleCreatedEvent(BaseModel):
    event_id: int
    type: EventType = EventType.cycle_created
    driver_id: str
    invoice_id: str
    week: int
    amount_due: int
    currency: str
    due_date: str
    discount_percent: int = 0


class PaymentReceivedEvent(BaseModel):
    event_id: int
    type: EventType = EventType.payment_received
    driver_id: str
    invoice_id: str
    payment_reference: str
    amount: int
    currency: str


class DiscountAppliedEvent(BaseModel):
    event_id: int
    type: EventType = EventType.discount_applied
    driver_id: str
    discount_percent: int
    used: bool = False  # True once consumed by the next cycle


class InvoiceCounter(BaseModel):
    """Tracks the next invoice number so IDs are always unique and sequential."""
    next_number: int = 1

    def generate(self, driver_id:str) -> str:
        invoice_id = f"INV-{driver_id}-{self.next_number:04d}"
        self.next_number += 1
        return invoice_id


# ─────────────────────────────────────────────
#  BILLING CYCLES  (API request / response)
# ─────────────────────────────────────────────
class CreateCycleRequest(BaseModel):
    driver_id: str
    week: int
    currency: str

    @field_validator("currency")
    @classmethod
    def currency_must_be_kes(cls, value: str) -> str:
        if value.upper() != CURRENCY:
            raise ValueError(f"currency must be {CURRENCY}, got {value}")
        return value.upper()

    @field_validator("week")
    @classmethod
    def week_must_be_positive(cls, value: int) -> int:
        if value < 1:
            raise ValueError("week must be 1 or greater")
        return value


class CycleResponse(BaseModel):
    invoice_id: str
    driver_id: str
    week: int
    amount_due: int
    currency: str
    due_date: str
    status: CycleStatus
    discount_applied: bool


# ─────────────────────────────────────────────
#  PAYMENTS  (API request / response)
# ─────────────────────────────────────────────
class CreatePaymentRequest(BaseModel):
    invoice_id: str
    payment_reference: str
    amount: int
    currency: str

    @field_validator("currency")
    @classmethod
    def currency_must_be_kes(cls, value: str) -> str:
        if value.upper() != CURRENCY:
            raise ValueError(f"currency must be {CURRENCY}, got {value}")
        return value.upper()

    @field_validator("amount")
    @classmethod
    def amount_must_be_positive(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("amount must be greater than zero")
        return value


class PaymentResponse(BaseModel):
    payment_reference: str
    invoice_id: str
    amount: int
    currency: str
    status: str  # "recorded" for new, "duplicate" for repeat
    message: str


# ─────────────────────────────────────────────
#  DISCOUNTS  (API request / response)
# ─────────────────────────────────────────────
class CreateDiscountRequest(BaseModel):
    driver_id: str
    discount_percent: int
    currency: str

    @field_validator("currency")
    @classmethod
    def currency_must_be_kes(cls, value: str) -> str:
        if value.upper() != CURRENCY:
            raise ValueError(f"currency must be {CURRENCY}, got {value}")
        return value.upper()

    @field_validator("discount_percent")
    @classmethod
    def discount_must_be_valid(cls, value: int) -> int:
        if value <= 0 or value > 100:
            raise ValueError("discount_percent must be between 1 and 100")
        return value


class DiscountResponse(BaseModel):
    driver_id: str
    discount_percent: int
    applies_to_next_cycle: bool
    message: str


# ─────────────────────────────────────────────
#  CYCLE LISTING  (GET /billing/cycles/{driver_id})
# ─────────────────────────────────────────────
class CycleSummaryItem(BaseModel):
    invoice_id: str
    week: int
    amount_due: int
    currency: str
    due_date: str
    status: CycleStatus


class CycleListResponse(BaseModel):
    driver_id: str
    cycles: list[CycleSummaryItem]


# ─────────────────────────────────────────────
#  SUMMARY  (GET /billing/summary/{driver_id})
# ─────────────────────────────────────────────
class SummaryResponse(BaseModel):
    driver_id: str
    total_billed: int
    total_paid: int
    total_outstanding: int
    missed_payment_count: int
    status: AccountStatus


# ─────────────────────────────────────────────
#  TEST SUPPORT
# ─────────────────────────────────────────────
class ResetResponse(BaseModel):
    status: str
    driver_loaded: int
    events_loaded: int
