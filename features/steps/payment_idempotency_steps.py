import requests
from behave import given, when, then


@given('driver "{driver_id}" has an active lease')
def step_driver_active_lease(context, driver_id):
    context.driver_id = driver_id


@given('a billing cycle exists for driver "{driver_id}" for week {week:d}')
def step_billing_cycle_exists(context, driver_id, week):
    response = requests.post(
        f"{context.base_url}/billing/cycles",
        json={
            "driver_id": driver_id,
            "week": week,
            "currency": "KES"
        }
    )
    assert response.status_code == 201, (
        f"Failed to create billing cycle for week {week}: {response.text}"
    )
    context.invoice_id = response.json()["invoice_id"]
    context.driver_id = driver_id


@given('a payment of {amount:d} KES has already been made with reference "{reference}"')
def step_payment_already_made(context, amount, reference):
    response = requests.post(
        f"{context.base_url}/billing/payments",
        json={
            "invoice_id": context.invoice_id,
            "payment_reference": reference,
            "amount": amount,
            "currency": "KES"
        }
    )
    assert response.status_code == 201, (
        f"First payment failed: {response.text}"
    )
    summary = requests.get(
        f"{context.base_url}/billing/summary/{context.driver_id}"
    )
    context.total_paid_before = summary.json()["total_paid"]


@when('a payment of {amount:d} KES is submitted with reference "{reference}"')
def step_submit_payment(context, amount, reference):
    context.response = requests.post(
        f"{context.base_url}/billing/payments",
        json={
            "invoice_id": context.invoice_id,
            "payment_reference": reference,
            "amount": amount,
            "currency": "KES"
        }
    )


@when('the same payment is submitted again with reference "{reference}"')
def step_submit_duplicate_payment(context, reference):
    context.response = requests.post(
        f"{context.base_url}/billing/payments",
        json={
            "invoice_id": context.invoice_id,
            "payment_reference": reference,
            "amount": 3500,
            "currency": "KES"
        }
    )


@then('the payment status should be "{expected_status}"')
def step_check_payment_status(context, expected_status):
    body = context.response.json()
    assert body["status"] == expected_status, (
        f"Expected status '{expected_status}', got '{body['status']}'"
    )


@then('the payment reference in the response should be "{reference}"')
def step_check_payment_reference(context, reference):
    body = context.response.json()
    assert body["payment_reference"] == reference, (
        f"Expected reference '{reference}', got '{body['payment_reference']}'"
    )


@then('the message should confirm no duplicate credit was applied')
def step_check_no_duplicate_message(context):
    body = context.response.json()
    assert "already recorded" in body["message"], (
        f"Expected 'already recorded' in message, got: {body['message']}"
    )


@then('the billing summary total paid should not have increased')
def step_check_total_paid_unchanged(context):
    summary = requests.get(
        f"{context.base_url}/billing/summary/{context.driver_id}"
    )
    total_paid_after = summary.json()["total_paid"]
    assert total_paid_after == context.total_paid_before, (
        f"Total paid increased after duplicate payment. "
        f"Before: {context.total_paid_before}, After: {total_paid_after}. "
        f"Duplicate credit was applied — this is a P0 bug."
    )