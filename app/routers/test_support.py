from app.store import store
from fastapi import APIRouter

router = APIRouter(prefix="/test", tags=["test_support"])


@router.post("/reset")
def reset_stub():
    """Wipe all data and reload seed data. Called before every test run."""
    with store.lock:
        store.reset()
        return {
            "status": "reset",
            "drivers_loaded": len(store.leases),
            "events_loaded": len(store.events),
        }
