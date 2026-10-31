from datetime import date

# The only currency this system accepts
CURRENCY = "KES"

# Fixed weekly lease amount, in whole Kenyan Shillings
WEEKLY_LEASE_AMOUNT = 3500

# A driver is flagged overdue after this many consecutive missed payments
OVERDUE_THRESHOLD = 3

# Week 1 of billing starts on this date (a Monday)
BILLING_START_DATE = date(2026, 1, 5)

# Maximum number of active pending discounts allowed per driver at one time
MAX_PENDING_DISCOUNTS = 1