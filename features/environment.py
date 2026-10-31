import requests

BASE_URL = "http://localhost:8000"


def before_scenario(context, scenario):
    """
        Reset the stub service before every scenario.
        This guarantees every scenario starts from the same
        known seed data — no leftover state from previous tests.
        """
    context.base_url = BASE_URL
    response = requests.post(f"{BASE_URL}/test/reset")

    assert response.status_code == 200, (
        f"Reset failed before scenario '{scenario.name}' "
        f"— is the stub running on {BASE_URL}?"
    )


def after_scenario(context, scenario):
    """
        Log scenario result for visibility.
        """
    status = "PASSED" if scenario.status == "passed" else "FAILED"
    print(f"\n[{status}] {scenario.name}")
