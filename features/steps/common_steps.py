import requests
from behave import given, then


@given('the stub service is running')
def step_stub_running(context):
    response = requests.get(f"{context.base_url}/health")
    assert response.status_code == 200, (
        f"Stub service is not running at {context.base_url}"
    )


@then('the response status code should be {status_code:d}')
def step_check_status_code(context, status_code):
    assert context.response.status_code == status_code, (
        f"Expected {status_code}, got {context.response.status_code}. "
        f"Response: {context.response.text}"
    )