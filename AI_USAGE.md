# AI Usage Log

**Author:** Preetam Kumar Sahu
**Challenge:** Greenwheels Senior Quality Engineer Take-Home Case Study
**Date:** October 2026

---

## Which AI Tool Was Used

| Tool | Purpose |
|---|---|
| Claude by Anthropic (Sonnet 4.6) | Main AI assistant used throughout the entire challenge |

---

## Where AI Saved the Most Time

### 1. Writing the Test Plan
AI wrote the first draft of the test plan — the risk table, the list of what is in and out of scope, the entry and exit criteria, and the scale section. I then read through it, simplified the language, and corrected parts that were too technical or unclear.

**Time saved:** About 2 hours.

### 2. Designing the Data Shapes
AI suggested splitting the project into two types of data shapes — one set for what happens inside the system (events like "payment made" or "cycle created") and a separate set for what the API sends and receives. This made the code much cleaner and easier to understand. I would not have thought to separate them that way from the start.

**Time saved:** About 1 hour.

### 3. Writing the Postman Collection
The Postman test file is written in a very specific JSON format. Writing it by hand is slow and easy to get wrong. AI generated the full file including all 63 checks, the logic that saves the invoice ID from one test and passes it to the next test automatically, and the folder structure.

**Time saved:** About 3 hours.

### 4. Writing the BDD Test Scenarios
AI wrote the first version of both plain English test files — the scenarios, the Examples tables with multiple data rows, and the Background sections that run before every test. The overdue flag boundary tests (1 missed payment, 2, 3, 4, 5) were also AI-suggested.

**Time saved:** About 1 hour.

### 5. Writing the GitHub Actions Pipeline
AI wrote the CI pipeline file — including the part that waits up to 60 seconds for the fake API to start before running the tests, the 5-second timeout on each API call, and the step that prints error logs if a test fails.

**Time saved:** About 1 hour.

---

## Where AI Got It Wrong — and What I Did Instead

### 1. The payment check was always returning False
AI suggested a way to check whether an event in the system was a payment event. The approach it suggested worked in simple tests but failed silently in the real app because of the way Python loads files — it ended up creating two copies of the same class in memory and the check always returned False even when the data was clearly there.

AI tried three different fixes that all failed. The solution I eventually landed on was to stop asking "is this a payment event?" and instead ask "does this event have a payment reference field?" — because only payment events have that field. This is a subtler and more reliable approach.

### 2. Test order caused a failure in the Postman collection
AI wrote the discount tests without realising that an earlier test (HP-04) had already applied a discount to DRIVER-001. So when the discount rule tests tried to apply a new discount, the system correctly rejected it with "discount already pending" — making the test fail for the wrong reason.

The fix was to add an extra step before the discount tests to use up the discount from HP-04 first. AI missed this connection — I caught it by running the tests and reading the output carefully.

### 3. Wrong quote marks in the test scenarios
AI wrote the plain English test files using curly quote marks (the kind a word processor uses) instead of straight quote marks (the kind code needs). The test tool could not match the steps to the step definitions and reported them all as missing. The files had to be rewritten with correct quote marks.

### 4. The PowerShell script did not work on Windows
AI wrote a test script using special characters (long dashes and curly quotes) that Windows terminals cannot handle. The characters showed up as garbage text and some commands were printed instead of run. The script had to be rewritten using only basic characters.

### 5. The scale section was too technical
The first version of the scale section used words like "WAL throughput", "materialised views", and "connection pool contention" — words that mean nothing to most people. I asked for a complete rewrite in plain English where every concept is explained with a simple analogy. This made the document much more useful.

---

## Checks That AI Missed — Added by Me

### 1. No test for terminated lease in the Postman collection
AI only wrote a test for a paused lease (DRIVER-002). It never added a test for a terminated lease (DRIVER-003). I noticed this gap and documented it in DEFECTS.md as a known missing test case.

### 2. Missing the "below threshold" tests for overdue
AI only wrote overdue tests for 3, 4, and 5 missed payments. I added the cases for 1 and 2 missed payments — these prove the system does NOT flag a driver overdue when they are below the limit. Without these, you only know the rule turns on, not that it stays off when it should.

### 3. No check that the reset actually loaded data
AI wrote the reset call at the start of the tests but did not check the response. I added a check that confirms `drivers_loaded` is greater than 0 — so if the reset fails silently, the tests catch it immediately instead of failing with confusing errors later.

### 4. Missing the `discount_applied: false` check
AI's test for "discount should not carry over to the next invoice" only checked that the invoice amount was the full price (3500). I added an extra check that `discount_applied` is explicitly false — because an amount of 3500 could accidentally pass even if the field was missing from the response entirely.

---

## Summary

AI was most useful for the repetitive, structured parts of the work — writing JSON files, YAML files, and documentation drafts. The parts where human judgement made the real difference were:

- Debugging why the payment check was silently returning the wrong answer
- Spotting that test order was causing a false failure in the discount tests
- Choosing which bugs to plant and making sure they were realistic and meaningful
- Making sure the language in every document was clear enough for anyone to understand
- Adding the boundary tests that prove what the system does NOT do, not just what it does

Total time spent: about 8 hours. Without AI it would have taken 14 to 16 hours for the same result.