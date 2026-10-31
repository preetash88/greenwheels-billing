from fastapi import FastAPI

from app.routers import test_support, billing_cycles, payments, discounts, summary

app = FastAPI(
    title="Greenwheels Billing Stub",
    description="A simplified fake of the Greenwheels billing API, built for QA testing.",
    version="1.0.0",
)

app.include_router(test_support.router)
app.include_router(billing_cycles.router)
app.include_router(payments.router)
app.include_router(discounts.router)
app.include_router(summary.router)


@app.get("/health", tags=["health"])
def health():
    """Used by CI to check the service is up before running tests."""
    return {"status": "ok"}
