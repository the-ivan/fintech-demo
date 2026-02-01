import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app, idempotency_store, payments_db


@pytest.fixture(autouse=True)
def clear_storage():
    """Clear in-memory storage before each test."""
    payments_db.clear()
    idempotency_store.clear()
    yield
    payments_db.clear()
    idempotency_store.clear()


@pytest.fixture
async def client():
    """Async test client for FastAPI app."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.fixture
def valid_payment_data():
    """Valid payment request data."""
    return {
        "amount": "100.00",
        "currency": "USD",
        "state": "CA",
        "recipient_id": "user-123",
        "description": "Test payment",
    }
