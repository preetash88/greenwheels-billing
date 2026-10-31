# Greenwheels QA Engineering Challenge
**Senior Quality Engineer — Take-Home Case Study**
**Author:** Preetam Kumar Sahu
**Date:** October 2026

---

## What Is This Project?

Greenwheels is a company that rents out electric motorcycles to drivers in Kenya, Ghana, and Uganda. Drivers pay weekly until they own the bike.

This project tests the **Billing Cycle feature** — the part of the system that:
- Works out how much a driver owes each week
- Creates an invoice for them
- Records when a payment is made
- Applies discounts
- Tracks missed payments

Because we cannot test against the real Greenwheels system (it has real money and real drivers), we built a **fake version of it** called a stub service. It behaves exactly like the real thing but runs on your laptop and uses pretend data.

---

## What Is Inside This Project?

```
stub/
├── app/                          # The fake API we built for testing
│   ├── main.py                   # Starts the fake API
│   ├── config.py                 # All the billing rules in one place
│   ├── schemas.py                # Defines what every request and response must look like
│   ├── store.py                  # Stores all the fake data in memory
│   └── routers/
│       ├── cycles.py             # Handles: create a billing cycle
│       ├── payments.py           # Handles: record a payment
│       ├── cycle_listing.py      # Handles: list all cycles for a driver
│       ├── discounts.py          # Handles: apply a discount
│       ├── summary.py            # Handles: get a driver's financial summary
│       └── test_support.py       # Handles: reset everything back to the start
├── features/                     # Plain English tests (BDD)
│   ├── payment_idempotency.feature  # Tests: same payment must never be credited twice
│   ├── overdue_flag.feature         # Tests: 3 missed payments triggers overdue status
│   ├── environment.py               # Resets the fake API before every test automatically
│   └── steps/
│       ├── common_steps.py              # Steps shared by both test files
│       ├── payment_idempotency_steps.py # Steps for the payment tests
│       └── overdue_flag_steps.py        # Steps for the overdue tests
├── postman/
│   ├── collection.json           # 63 automated API checks
│   └── env.json                  # Settings like the server address and test driver IDs
├── .github/
│   └── workflows/
│       └── qa.yml                # Runs all tests automatically when code is pushed
├── Dockerfile                    # Instructions to package the fake API into a container
├── docker-compose.yml            # One command to start everything
├── requirements.txt              # List of Python packages needed
├── TEST_PLAN.md                  # Full testing strategy and what risks we looked at
├── DEFECTS.md                    # Two bugs we planted on purpose, documented as real bugs
├── AI_USAGE.md                   # Honest log of where AI helped and where it failed
└── README.md                     # This file
```

---

## How to Get Started

### What You Need First

- **Docker Desktop** — download from docker.com and make sure it is running
- **Node.js** — needed to run Newman (the tool that runs our API tests)
- **Python 3.14** with uv — needed to run the plain English BDD tests

### Step 1 — Start the fake API

Open a terminal, go into the `stub` folder, and run:

```bash
docker-compose up --build
```

Wait until you see this line:
```
greenwheels-stub | INFO:     Application startup complete.
```

The fake API is now running at `http://localhost:8000`.

You can also open `http://localhost:8000/docs` in your browser to see and try all the API endpoints interactively.

### Step 2 — Check it is working

```bash
curl http://localhost:8000/health
```

You should see:
```json
{"status": "ok"}
```

### Step 3 — Load the starting data

```bash
curl -X POST http://localhost:8000/test/reset
```

You should see:
```json
{"status": "reset", "drivers_loaded": 4, "events_loaded": 4}
```

This loads four pretend drivers into the system so the tests have someone to bill.

---

## Running the API Tests

These tests check every endpoint automatically and tell you instantly if something is wrong.

Install the test runner (one time only):
```bash
npm install -g newman
```

Run all tests:
```bash
newman run postman/collection.json --environment postman/env.json
```

You should see:
```
assertions: 63 executed, 0 failed
```

> **Important:** This project has two bugs planted in it on purpose (see DEFECTS.md).
> When the bugs are active, 2 of the 63 checks will fail — this is intentional and
> shows the tests are doing their job by catching real problems.

---

## Running the Plain English BDD Tests

BDD tests are written in plain English so anyone can read them and understand what is being tested, not just developers.

Install the tools (one time only):
```bash
uv venv --python 3.14
source .venv/bin/activate        # On Windows: .venv\Scripts\activate
uv pip install -r requirements.txt
```

Run all tests:
```bash
behave features/
```

Run just one test file:
```bash
behave features/payment_idempotency.feature
behave features/overdue_flag.feature
```

You should see:
```
2 features passed, 0 failed
16 scenarios passed, 0 failed
```

---

## The 5 API Endpoints

| What it does | How to call it |
|---|---|
| Create a weekly invoice for a driver | `POST /billing/cycles` |
| Record that a driver paid | `POST /billing/payments` |
| See all invoices for a driver | `GET /billing/cycles/{driver_id}` |
| Give a driver a discount on their next invoice | `POST /billing/discounts` |
| See a driver's total billed, paid, and missed payments | `GET /billing/summary/{driver_id}` |
| Wipe all data and reload starting data | `POST /test/reset` |
| Check if the service is running | `GET /health` |

---

## The Starting Drivers (Seed Data)

When you reset the system, these four drivers are loaded automatically:

| Driver | Lease Status | What They Are Used For |
|---|---|---|
| DRIVER-001 | Active — has 2 paid invoices | Main driver for happy path tests |
| DRIVER-002 | Paused | Tests: cannot bill a paused lease |
| DRIVER-003 | Terminated | Tests: cannot bill a terminated lease |
| DRIVER-004 | Active — no history | Tests: overdue and discount tests (clean slate) |

---

## The 5 Business Rules We Test

| Rule | What it means in plain English |
|---|---|
| No billing for inactive drivers | If a driver's lease is paused or cancelled, the system must refuse to create an invoice |
| No double payments | If a payment is submitted twice with the same reference code, only the first one counts |
| Three missed payments = overdue | If a driver misses 3 payments in a row, the system flags their account as overdue |
| Discount only applies once | A discount applies to the very next invoice only — it does not carry over or stack with other discounts |
| KES only | Every transaction must use Kenyan Shillings — any other currency is rejected |

---

## The Two Bugs We Planted

We deliberately introduced two bugs into the fake API to show that our tests can catch real problems. Full details are in `DEFECTS.md`.

| Bug | What it does | How bad |
|---|---|---|
| DEFECT-001 | Discount is accepted but silently never actually applied to the invoice | Critical — drivers are overcharged without knowing |
| DEFECT-002 | A terminated lease returns the wrong error code (404 instead of 409) | Medium — the action is blocked correctly but the wrong error is shown |

---

## Why We Chose These Tools

| Tool | What it is | Why we used it |
|---|---|---|
| FastAPI | A Python tool for building APIs quickly | Fast to write, gives us a free interactive docs page, matches the real system's language |
| Docker | Packages the app so it runs the same everywhere | Anyone can start the fake API with one command — no setup required |
| Postman / Newman | A tool for testing APIs | Easy to write tests, runs from the command line, works in CI |
| Behave | A tool for writing tests in plain English | Non-developers can read and understand the tests |
| GitHub Actions | Runs tests automatically when code changes | Catches broken code before it reaches the main branch |

---

## Things We Assumed

1. The fake API responds instantly — in the real system there might be a tiny delay between saving a payment and seeing it in the summary
2. Any token in the Authorization header is accepted — real security testing is out of scope
3. Only KES currency is valid — no other currencies
4. A missed payment means an invoice that is past its due date with no payment recorded
5. The reset endpoint always loads all four drivers correctly

---

## Gaps We Are Aware Of

- We test the paused lease rule but not the terminated lease rule in the Postman collection — adding a test for DRIVER-003 would close this gap
- Only KES rules are tested — Ghana and Uganda have different currencies and may have different rules
- No real login or security testing — the token is a placeholder
- Performance testing (testing how fast the system runs under heavy load) is written up as a plan in TEST_PLAN.md but not actually run