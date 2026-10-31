# TEST PLAN — Greenwheels Billing Cycle Feature

**Author:** Preetam Kumar Sahu
**Version:** 2.0
**Date:** October 2026
**System Under Test:** Greenwheels Core Fleet Ops — Billing Cycle API

---

## 1. Introduction

Greenwheels is an electric motorcycle leasing company operating across Kenya, Ghana, and Uganda with over 2,200 active drivers. Drivers lease motorcycles on a weekly payment plan until they own the bike outright.

The system that runs the business is built in Python and uses a database called PostgreSQL on AWS. It manages everything from the moment a driver joins, through lease creation, billing, and payment tracking.

This test plan covers the **Billing Cycle feature** — the part of the system that:
- Calculates how much a driver owes each week
- Applies discounts when applicable
- Generates an invoice for the driver
- Records whether a payment was made or missed

### What does "event-sourced" mean and why does it matter for testing?

The system does not store the current state of a driver's account directly. Instead, it stores a **history of everything that has happened** — every payment made, every payment missed, every lease pause — as a permanent record. When you ask "what is this driver's balance?", the system reads through all those historical records and calculates the answer fresh each time.

**Why this matters for testing:**
- We cannot look directly into the database to check if something worked
- The only way to verify that something happened correctly is to call an API endpoint and read the result
- Every test must set up its data by calling the API first, not by inserting data directly into a database
- The order in which we make API calls matters — doing things out of order will give us wrong results
- A duplicate payment recorded in this system is very hard to undo because all historical records are permanent

---

## 2. Scope

### 2.1 What We Are Testing

| Area | What This Means |
|---|---|
| 5 API Endpoints | The five billing endpoints: create cycle, record payment, list cycles, apply discount, get summary |
| 5 Business Rules | All the rules the business has defined for billing behaviour |
| Functional Tests | Does each endpoint do what it is supposed to do? |
| Negative Tests | What happens when we send bad or missing data? Does the system reject it correctly? |
| Boundary Tests | What happens exactly at the edge — e.g., at exactly 3 missed payments, not 2 and not 4? |
| Integration Tests | Do multiple endpoints work correctly together in sequence? |
| Regression Tests | Automated checks that run every time a code change is made, to catch things that break |
| BDD Scenarios | Two business rules written out as plain-English test scenarios in Gherkin format |
| Stub Service | A simplified fake version of the real API that we build ourselves for testing purposes |
| Defect Report | Two intentional bugs we plant in our own stub service, documented as real defect reports |
| CI Pipeline | An automated system that runs our tests on GitHub every time someone opens a pull request |
| Scale Thinking | Written analysis (no code) of how the testing approach changes when the system grows to 500,000 drivers |

### 2.2 What We Are NOT Testing

| Area | Why It Is Out of Scope |
|---|---|
| Driver sign-up and onboarding | This is a separate part of the system, not part of billing |
| Vehicle inspection and intake | Another separate feature domain |
| The real production database | We test through the API only — no direct database access |
| Any user interface or frontend | No frontend is provided for this challenge |
| Performance testing (running actual load tests) | Covered as a written design exercise only in Section 8 |
| Ghana and Uganda billing rule differences | The stub service only implements Kenya (KES) rules for now |

---

## 3. Risk Assessment

Before writing any tests, I looked at every part of the billing feature and asked: **"If this breaks, how bad would it be, and how likely is it to break?"**

The areas with the highest risk get the most test coverage.

### 3.1 Risk Table

| # | What Could Go Wrong | How Likely | How Bad | Priority | Plain English Explanation |
|---|---|---|---|---|---|
| R1 | **Duplicate payment credited to a driver's account** | High | Critical | P0 | If the same payment is recorded twice, the driver gets double credit — the company loses money. In this system, historical records cannot be deleted, so this kind of mistake is very hard to fix. This is the most dangerous risk. |
| R2 | **Overdue flag triggering at the wrong number of missed payments** | High | High | P1 | The rule says a driver is flagged overdue after 3 consecutive missed payments. If the system flags them at 2 (too early), good drivers get locked out unfairly. If it waits until 4 (too late), bad drivers get more credit than they should. This type of "one-off" error is one of the most common bugs in software. |
| R3 | **Billing cycle created for a paused or cancelled lease** | Medium | Critical | P1 | If a driver's lease is paused or cancelled and the system still charges them, it creates a legal problem and damages driver trust. This guard must never fail. |
| R4 | **A discount applying to two weeks instead of one, or two discounts stacking** | Medium | High | P1 | The rule is that a discount applies to the next week's invoice only and cannot be combined with another discount. If this fails, the company quietly loses money every week it goes unnoticed. |
| R5 | **Wrong currency accepted by the system** | Medium | High | P2 | All amounts must be in KES (Kenyan Shillings). If the system accepts USD or GHS without rejecting them, financial records become incorrect across countries as Greenwheels expands. |
| R6 | **The summary endpoint showing old data after a payment is made** | Low | High | P2 | Because the system builds its view from historical records, there is a small chance the summary is not updated immediately after a payment. This could cause tests to fail even when the system is actually correct. |
| R7 | **Invoice amount calculated incorrectly** | Low | High | P2 | If the weekly amount or discounted amount is wrong, drivers are charged incorrectly. This is most risky when a discount is being applied — the arithmetic must be verified. |
| R8 | **CI pipeline showing "all passed" when tests actually failed** | Low | Medium | P3 | If the automated test pipeline gives a false green result, the team loses confidence in it and bugs can slip through to production. |

---

## 4. Test Approach

### 4.1 Types of Tests We Will Write

**Functional Tests — Does it do what it is supposed to do?**
- Each endpoint returns the correct HTTP status code (e.g., 200 for success, 404 when something is not found)
- Each response contains the correct fields and values
- All 5 business rules work correctly

**Negative Tests — What happens when we send bad data?**
- Missing required fields → system should return `400 Bad Request`
- Wrong currency (e.g., USD instead of KES) → system should reject it
- Same payment reference sent twice → system should not credit the payment a second time
- Trying to create a billing cycle for a paused or cancelled lease → system should block it
- Asking for a driver that does not exist → system should return `404 Not Found`

**Boundary Tests — What happens right at the edge of a rule?**
- 2 missed payments → driver must NOT be marked overdue
- 3 missed payments → driver MUST be marked overdue
- 4 missed payments → driver must STILL be marked overdue (not reset)
- Applying a discount, then applying another discount in the same week → the second must not stack
- A discount applied this week must NOT appear in a cycle two weeks from now

**Integration / Flow Tests — Do multiple steps work correctly together?**
- Create a billing cycle → record a payment → check that the summary shows the correct totals
- Create 3 billing cycles with no payments → check that the overdue flag appears in the summary
- Apply a discount → generate next week's cycle → confirm the discounted amount → generate the week after → confirm the discount is gone

**Regression Tests — Automated checks that run on every code change**
- All 5 business rules are tested automatically in our Postman / Newman collection
- These run through GitHub Actions on every pull request, so broken code cannot be merged undetected

### 4.2 How We Handle Testing an Event-Sourced System

Because the system stores a history of events rather than a current state, our testing approach follows these five rules:

1. **Always check results through the API, not the database.** After making a payment, we verify it by calling the summary endpoint — not by looking at a database table.

2. **Set up all test data through the API.** If we need a driver with 3 missed payments, we must actually create 3 billing cycles with no payments through the API — no database shortcuts.

3. **The order of API calls is part of the test.** Doing step 2 before step 1 may give completely different results. The sequence is intentional and must be followed exactly.

4. **Duplicate payment records are the most dangerous bug.** Every payment event is stored permanently and replayed each time the summary is calculated. A duplicate event means the driver gets double credit permanently — and it is very difficult to remove.

5. **Allow for timing.** In some event-sourced systems, there is a short delay between recording an event and seeing it in the summary. Our stub service will be synchronous (instant), but we document this as a risk in the real system.

---

## 5. Test Cases Summary

### 5.1 Happy Path Tests — The Normal Working Cases

| Test ID | Endpoint | What We Are Testing |
|---|---|---|
| HP-01 | `POST /billing/cycles` | Create a billing cycle for a driver with an active lease. Check that we get back an invoice ID, the amount owed, the currency (KES), and a due date. |
| HP-02 | `POST /billing/payments` | Record a valid payment against an invoice. Check that the payment is accepted and the invoice status changes to paid. |
| HP-03 | `GET /billing/cycles/{driver_id}` | Get the list of all billing cycles for a driver. Check that the list is returned with the correct status on each cycle. |
| HP-04 | `POST /billing/discounts` | Apply a discount for an eligible driver. Check that the system accepts it and confirms the discount will apply to the next cycle. |
| HP-05 | `GET /billing/summary/{driver_id}` | Get the financial summary for a driver. Check that total billed, total paid, total outstanding, and missed payment count are all returned correctly. |

### 5.2 Business Rule Tests — One Test Per Rule

| Test ID | Business Rule | What We Do | What We Expect |
|---|---|---|---|
| BR-01 | Paused or terminated lease cannot be billed | Try to create a billing cycle for a driver whose lease is paused | System rejects it with a 409 or 422 error — no cycle is created |
| BR-02 | Same payment cannot be credited twice | Record a payment. Then record the exact same payment again using the same reference code | Second request is accepted without error, but the driver's paid total does NOT increase a second time |
| BR-03 | Three missed payments triggers overdue status | Create 3 billing cycles for a driver with no payments | Summary shows missed payment count = 3 and driver status = overdue |
| BR-04 | Discount applies to next week only and does not stack | Apply a discount. Create next week's cycle (should be discounted). Create the week after (should be full price) | Week N+1 shows the discounted amount. Week N+2 shows the full price. |
| BR-05 | Only KES currency is accepted | Try to create a billing cycle and send the currency as USD | System rejects it with a 400 or 422 error |

### 5.3 Negative and Edge Case Tests

| Test ID | What We Do | What We Expect |
|---|---|---|
| NEG-01 | Create a billing cycle without sending a driver ID | System returns 400 — required field is missing |
| NEG-02 | Record a payment without a payment reference | System returns 400 — required field is missing |
| NEG-03 | Record a payment against an invoice ID that does not exist | System returns 404 — invoice not found |
| NEG-04 | Apply a discount for a driver who is not eligible | System returns 422 — discount eligibility check failed |
| NEG-05 | Request billing cycles for a driver ID that does not exist | System returns 404 — driver not found |
| NEG-06 | Try to create a billing cycle for a week that has already been billed | System returns 409 — duplicate cycle for same driver and week |
| NEG-07 | Record a payment with an amount of zero | System returns 400 — payment amount must be greater than zero |

---

## 6. The Stub Service We Are Building

Because Greenwheels has not provided a test service, we are building our own minimal fake version of the API. This is called a **stub service**.

### What is a stub service?

A stub service is a simplified fake version of the real API. It accepts the same requests and returns the same types of responses, but it runs on your local computer and uses simple in-memory storage instead of a real database. It is used purely for testing purposes.

### What our stub service does

- Implements all 5 billing API endpoints
- Enforces all 5 business rules so our tests have something real to check against
- Includes two drivers as pre-loaded seed data:
  - **Driver A (DRIVER-001):** Active lease, with some existing billing cycles already created
  - **Driver B (DRIVER-002):** Paused lease, used to test the rule that blocks billing for inactive drivers
- Includes a special reset endpoint (`POST /test/reset`) that clears all data and reloads the seed data — called by our CI pipeline before each test run so tests always start from a known, clean state

### Two intentional bugs we have planted in the stub

As part of this challenge, we introduced two intentional defects into the stub service and documented them as real defect reports in DEFECTS.md:

- **Bug 1:** A silent business rule violation — the system appears to work correctly but breaks a rule without showing an error
- **Bug 2:** An incorrect HTTP status code — the system returns the wrong error code, making it look like a different kind of problem than it actually is

These bugs exist only in the stub to fulfil the requirements of this challenge. They would not exist in a properly reviewed production service.

### Technology choice

The stub is written in **Python using FastAPI** because:
- It is fast to write and easy to read
- FastAPI automatically validates request data and returns clear error messages
- Python matches the technology the real Greenwheels backend uses
- The stub starts in seconds with a single Docker command

---

## 7. Entry and Exit Criteria

### Before Testing Starts (Entry Criteria)

These things must all be true before we run any tests:

- [ ] The stub service starts with `docker-compose up` and shows no errors
- [ ] All 5 API endpoints return a response (even if it is an error — the service must be reachable)
- [ ] The environment file (`env.json`) is set up with the correct base URL and test driver IDs
- [ ] Newman is installed and the Postman collection loads without a configuration error
- [ ] `POST /test/reset` successfully reloads the seed data

### Before a Release Can Be Approved (Exit Criteria)

All of the following must be true before we sign off on a release:

- [ ] All 5 happy path tests pass
- [ ] All 5 business rule tests pass — zero failures allowed here
- [ ] All 7 negative / edge case tests pass
- [ ] No P0 or P1 defects are open (critical bugs must be fixed before release)
- [ ] The CI pipeline on the main branch is green — Newman exits with code 0
- [ ] Both Gherkin BDD feature files have been reviewed and approved
- [ ] Any P2 defects have a confirmed fix date or an agreed workaround

---

## 8. Scale Considerations

*This section is a written design exercise only. No code needs to be written.*

**The situation:** Greenwheels is growing to 5 countries with 500,000 active drivers. Every Sunday night, the system must create 500,000 invoices — one for each driver — within a 4-hour window.

---

### 8.1 What Would Break First at 500,000 Drivers

To create 500,000 invoices in 4 hours, the system needs to create about **35 invoices every single second** on average. At the start of the Sunday billing run, when everything kicks off at once, this number could be much higher.

Here is what I expect to fail first, in order from most to least likely:

---

**Problem 1 — The database gets overwhelmed (most likely to fail first)**

Think of the database like a single cashier at a supermarket. When 35 customers arrive every second, the queue builds up faster than the cashier can serve them. The system slows down, then stops.

This is made worse because Greenwheels never deletes or updates records — it only ever adds new ones. So every billing action creates a new row in the database. Over time the queue of new rows becomes enormous.

*How to spot it:* The system starts responding slowly. The first sign is that creating a billing cycle takes longer and longer — from 100 milliseconds to 1 second to 10 seconds. Set up an alert so the team is told automatically before the system completely stops.

---

**Problem 2 — Two invoices end up with the same ID**

Every invoice needs its own unique ID (like a ticket number). When 500,000 billing jobs all start at the same time and all ask for a new ticket number simultaneously, two of them might grab the same number at the same moment — like two people at a busy counter both reaching for the last numbered ticket at exactly the same time.

*How to spot it:* After a full billing run, count the invoice IDs. If you started with 500,000 drivers and ended up with fewer than 500,000 unique invoice IDs, some drivers got the same ID — which means one of them got someone else's invoice.

---

**Problem 3 — The summary page becomes very slow**

The summary endpoint works by reading every single past payment and adding them all up. For a driver who has been leasing for two years, that is more than 100 records to read just to show their balance. At 500,000 drivers all checking their summaries at the same time, this creates an enormous amount of reading work.

*How to spot it:* Time how long the summary endpoint takes to respond. If it goes from 1 second to 10 seconds or more, this is the cause.

---

**Problem 4 — The server runs out of memory**

If all 500,000 billing jobs start at exactly the same moment with nothing slowing them down or spacing them out, the server may simply run out of memory — like opening 500,000 browser tabs all at once on a laptop.

*How to spot it:* Watch the memory usage on the server. Set up a warning when memory gets too high, before the server crashes and takes everything down with it.

---

### 8.2 How I Would Test the System Under Heavy Load

**Tool I would use: k6**

k6 is a free tool that pretends to be thousands of users sending requests to the API at the same time. You write a simple script telling it how many fake users to send and when, and it measures how the system copes.

**The test plan:**

| Phase | What We Do | Why |
|---|---|---|
| Warm up (0 to 10 minutes) | Slowly increase from 0 to 500 pretend users | Mirrors how the real billing job starts up gradually |
| Hold steady (10 to 240 minutes) | Keep 500 pretend users going for 4 hours | This is the full Sunday night billing window |
| Sudden spike (at minute 30) | Jump to 2,000 users for 2 minutes | Tests what happens if every driver is billed at exactly the same moment |
| Wind down (240 to 250 minutes) | Gradually bring users back to 0 | Checks the system recovers cleanly after the busy period |

**What a passing result looks like:**

- 95 out of every 100 billing requests finish in under half a second
- 99 out of every 100 billing requests finish in under 1 second
- Fewer than 1 in every 1,000 requests ends in an error
- Every driver gets exactly one invoice — no duplicates, no missing invoices

---

### 8.3 How I Would Test That Duplicate Payments Are Caught at Scale

**The problem in plain English:**

A driver pays their weekly fee on their phone. Their internet drops for a second. The app automatically tries again. Now the same payment has been sent twice. The system must recognise it is the same payment and only count it once — not give the driver double credit.

At 500,000 payments per week, even 0.1% going wrong means 500 drivers getting double credit. That is real money the company loses.

**How I would test this:**

**Step 1 — Send fake duplicate payments on purpose**

In the load test, I would deliberately send the same payment twice for 0.1% of drivers. I would keep a note of exactly which payments were duplicated.

**Step 2 — Check the accounts afterwards**

For every driver whose payment was deliberately sent twice, I would check their account balance. It should show the correct amount paid — not double.

**Step 3 — The numbers must add up**

Simple example using 10,000 payments:

| What | Number |
|---|---|
| Total payment requests sent | 10,000 |
| Payments sent only once | 9,990 |
| Payments deliberately sent twice | 10 |
| Credits that should appear in accounts | 9,990 |
| Extra credits from duplicates (must be zero) | 0 |

If any driver's account shows more paid than they actually owe, the test fails.

**Step 4 — Test two payments arriving at exactly the same moment**

Send two identical payment requests within a few milliseconds of each other. This is the hardest case — the system has to handle two copies of the same payment arriving almost simultaneously. Only one credit should appear.

---

### 8.4 How I Would Keep the Tests Working Across Five Countries

**The problem:**

Kenya uses KES. Ghana uses GHS. Uganda uses UGX. Each country may also have slightly different rules — for example, Uganda might flag a driver overdue after 2 missed payments instead of 3.

If we write a completely separate set of tests for each country, we end up with five copies of the same tests. When a rule changes, we have to update it in five places instead of one. This is a maintenance nightmare.

**The solution: write the test once, swap the settings per country**

**Step 1 — Create one settings file per country**

```
config/ke.json  →  currency: KES,  overdue after: 3 missed payments
config/gh.json  →  currency: GHS,  overdue after: 3 missed payments
config/ug.json  →  currency: UGX,  overdue after: 2 missed payments
```

Each file only contains the things that are different per country.

**Step 2 — The test reads from the settings file**

For example, the currency check says:
> "The invoice currency must match whatever currency is set in the country settings file"

For Kenya it checks for KES. For Ghana it checks for GHS. The test itself never changes — only the settings file does.

**Step 3 — Run the tests once per country automatically**

The CI pipeline runs the full test suite three times in parallel — once for each country's settings file. If a rule breaks in Ghana but not Kenya, only Ghana's tests fail. This makes it immediately clear which country has a problem.

**Step 4 — Country-specific rules get their own test**

If Ghana has a rule that no other country has, that rule gets its own test clearly labelled "Ghana only". It only runs in Ghana's pipeline job. It does not affect the other countries.

**The result:**
- One rule changes for all countries → update one test → done
- One rule changes for one country → update that country's settings file → done
- No copying and pasting the same tests five times
- It is always clear what is shared and what is country-specific

---

## 9. Tools and Environment

| Tool | What We Use It For |
|---|---|
| Postman / Newman | Writing API tests and running them from the command line |
| GitHub Actions | Running tests automatically every time code changes |
| Docker | Starting the fake service with a single command |
| FastAPI (Python) | The framework we used to build our fake service |
| Behave | The tool that runs our plain English BDD test files |
| k6 | The tool we would use for load testing (design only for this challenge) |

---

## 10. Assumptions

The following things have been assumed. If any of them turn out to be wrong, this plan may need updating.

1. **The fake service responds instantly after a change.** In the real system, there might be a short delay between recording a payment and seeing it reflected in the summary. Our fake service has no delay. If the real system has a delay, tests will need to wait before checking the result.

2. **Any non-empty token is accepted.** The fake service does not check whether the login token is valid. Real security testing is out of scope.

3. **Only KES is accepted.** Any other currency must be rejected on every endpoint that accepts money.

4. **A missed payment means a billing cycle whose due date has passed with no payment recorded.** We have not confirmed this definition with the business team — it is our working assumption.

5. **The reset endpoint always restores all four starting drivers.** Our automated tests depend on this. If the reset fails silently, tests will produce confusing results.

6. **The due dates in the starting data are in the past.** This is intentional — it means any unpaid cycle is immediately treated as overdue, so we do not have to wait days to test the overdue rule.