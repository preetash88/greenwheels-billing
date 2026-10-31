import requests
from behave import given, when, then


@given('driver "{driver_id}" has an active lease with no billing history')
def step_driver_clean(context, driver_id):
    context.driver_id = driver_id


@given('driver "{driver_id}" has no billing cycles')
def step_driver_no_cycles(context, driver_id):
    context.driver_id = driver_id


@given('driver "{driver_id}" has {count:d} unpaid overdue billing cycles')
def step_create_unpaid_cycles(context, driver_id, count):
    context.driver_id = driver_id
    # Weeks 1-50 are all in the past (due dates in Jan-Dec 2026)
    # so any cycle created for these weeks is immediately overdue
    for week in range(1, count + 1):
        response = requests.post(
            f"{context.base_url}/billing/cycles",
            json={
                "driver_id": driver_id,
                "week": week,
                "currency": "KES"
            }
        )
        assert response.status_code == 201, f"Failed to create cycle for week {week}: {response.text}"

        # Deliberately do NOT record any payment
        # This makes each cycle an unpaid overdue cycle


@when('the billing summary is requested for driver "{driver_id}"')
def step_get_summary(context, driver_id):
    context.response = requests.get(
        f"{context.base_url}/billing/summary/{driver_id}"
    )


@then('the account status should be "{expected_status}"')
def step_check_account_status(context, expected_status):
    body = context.response.json()
    assert body["status"] == expected_status, (
        f"Expected account status '{expected_status}', "
        f"got '{body['status']}'. "
        f"Missed payment count: {body['missed_payment_count']}"
    )


@then('the missed payment count should be {expected_count:d}')
def step_check_missed_count(context, expected_count):
    body = context.response.json()
    assert body["missed_payment_count"] == expected_count, (
        f"Expected missed_payment_count {expected_count}, "
        f"got {body['missed_payment_count']}"
    )
