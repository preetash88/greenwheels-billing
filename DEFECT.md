# AI_USAGE.md — AI Tool Usage Log

**Author:** Preetam Kumar Sahu
**Challenge:** Greenwheels Senior Quality Engineer Take-Home Case Study
**Date:** October 2026

---

## Tools Used

| Tool | Version | Purpose |
|---|---|---|
| Claude (Anthropic) | Claude Sonnet 4.6 | Primary AI assistant throughout the challenge |

---

## Where AI Meaningfully Accelerated Work

### 1. TEST_PLAN.md — Structure and Scale Section
AI generated the initial structure of the test plan including the risk register table, entry/exit criteria, and scale considerations section. The scale section in particular — covering PostgreSQL write throughput bottlenecks, idempotency validation at 500k scale, and country-specific regression strategy — was drafted by AI and then reviewed and refined for accuracy.

**Time saved:** Approximately 2 hours of research and writing.

### 2. Pydantic Schema Design
AI suggested the separation of internal store models (`CycleCreatedEvent`, `PaymentReceivedEvent`, `DiscountAppliedEvent`) from API request/response schemas. This clean separation was not in the initial plan and improved the architecture significantly.

**Time saved:** Approximately 1 hour of design thinking.

### 3. Postman Collection JSON Structure
Writing Postman v2.1 collection JSON by hand is tedious and error-prone. AI generated the full collection structure including all 63 assertions, the request chaining logic (saving `invoice_id` as an environment variable in HP-01 for use in HP-02), and the folder organisation.

**Time saved:** Approximately 3 hours of JSON authoring.

### 4. BDD Gherkin Feature Files
AI generated the initial Gherkin scenarios for both feature files, including the `Scenario Outline` with `Examples` tables for the boundary condition tests. The `Background` sections and the structure of the overdue flag boundary tests (1, 2, 3, 4, 5 missed payments) were AI-suggested.

**Time saved:** Approximately 1 hour.

### 5. GitHub Actions YAML
AI generated the CI workflow structure including the health check retry loop, `--timeout-request 5000` Newman flag, `if: always()` on the cleanup step, and the two-job structure (api-tests, bdd-tests with `needs: api-tests`).

**Time saved:** Approximately 1 hour.

---

## Where AI Output Was Rejected or Corrected

### 1. isinstance vs hasattr for event type checking
AI initially suggested using `isinstance(e, PaymentReceivedEvent)` to filter events in the store. This caused a silent failure due to Python circular imports — the `isinstance` check returned `False` even when the objects matched, because two different copies of the class existed in memory.

AI went through three incorrect suggestions before the correct fix was identified: using `hasattr(e, "payment_reference")` to identify payment events by their unique fields rather than by class identity. This was a meaningful debugging exercise that required understanding Python's module loading behaviour.

### 2. Test order dependency in Postman collection
AI initially wrote the BR-04 (discount) tests without accounting for the fact that HP-04 had already applied a pending discount to DRIVER-001. This caused BR-04a to fail with 422 "discounts do not stack" instead of 201.

The fix required inserting a setup step to consume the HP-04 discount before BR-04a ran. AI missed this dependency — it was caught manually by running the collection and reading the Newman output carefully.

### 3. Smart quotes in Gherkin feature files
AI generated Gherkin with curly smart quotes (`"`) instead of straight quotes (`"`). Behave could not match these to step definitions and reported them as undefined steps. The feature files had to be rewritten with correct ASCII quotes.

### 4. PowerShell script encoding issues
AI generated a PowerShell test script using em dashes (`—`) and smart quotes which corrupted on Windows terminals. The script had to be rewritten using only plain ASCII characters.

### 5. Scale section language
The first version of the scale section used heavy technical jargon ("WAL throughput", "materialised views", "connection pool contention"). This was rejected and rewritten in plain English with analogies, because the purpose of the document is to communicate risk clearly to a mixed technical and non-technical audience.

---

## Test Cases and Assertions AI Missed — Added Manually

### 1. DRIVER-003 (terminated lease) gap in Postman collection
AI only generated BR-01 covering a paused lease (DRIVER-002). The terminated lease case (DRIVER-003) was not included. This was identified manually and documented in DEFECTS.md as a known gap — BR-01b should be added to complete Business Rule 1 coverage.

### 2. Boundary at exactly 2 missed payments
The Scenario Outline in `overdue_flag.feature` covers 1, 2, 3, 4, and 5 missed payments. AI initially only included 3, 4, and 5. The cases for 1 and 2 (proving the system does NOT flag overdue below threshold) were added manually — these are critical boundary conditions that prove the negative case.

### 3. `POST /test/reset` assertion in Newman setup
AI generated the reset call but without any assertion. The check that `drivers_loaded` is greater than 0 was added manually to ensure the reset actually loaded seed data, not just returned 200 with an empty store.

### 4. `discount_applied: false` assertion in BR-04c
AI's BR-04c test only checked `amount_due: 3500`. The additional assertion `discount_applied: false` was added manually to explicitly confirm the field itself is false — not just that the amount happens to be correct (which could pass even if the field was missing from the response).

---

## Overall Assessment

AI accelerated the mechanical parts of this challenge significantly — JSON authoring, YAML structure, boilerplate Gherkin, and documentation drafting. The areas where human judgement was essential were:

- Debugging the circular import issue with `isinstance`
- Identifying test order dependencies in the Postman collection
- Choosing which 2 bugs to plant and why they represent meaningful risk
- Ensuring the scale section communicated clearly rather than technically
- Adding boundary condition tests that prove the negative case

The challenge took approximately 8 hours total. Without AI assistance, the estimate would be 14-16 hours for the same quality of output.