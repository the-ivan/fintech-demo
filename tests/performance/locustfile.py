"""Load tests for Fintech Payment API."""

import uuid

from locust import HttpUser, between, constant, tag, task


class PaymentUser(HttpUser):
    """
    Standard user for load and soak testing.
    Simulates realistic payment creation with pauses between requests.
    """

    wait_time = between(1, 3)

    @task(3)
    @tag("payments", "load", "soak")
    def create_payment(self):
        """Create a new payment with unique idempotency key."""
        idempotency_key = str(uuid.uuid4())
        self.client.post(
            "/payments",
            json={
                "amount": "100.00",
                "currency": "USD",
                "state": "CA",
                "recipient_id": f"user-{uuid.uuid4().hex[:8]}",
                "description": "Load test payment",
            },
            headers={"X-Idempotency-Key": idempotency_key},
        )

    @task(1)
    @tag("health", "load", "soak")
    def health_check(self):
        """Check API health."""
        self.client.get("/health")


class SpikeUser(HttpUser):
    """
    Aggressive user for spike testing.
    No wait time between requests to simulate traffic bursts.
    """

    wait_time = constant(0)

    @task
    @tag("payments", "spike")
    def rapid_payment(self):
        """Create payments as fast as possible."""
        self.client.post(
            "/payments",
            json={
                "amount": "50.00",
                "currency": "USD",
                "state": "TX",
                "recipient_id": f"spike-{uuid.uuid4().hex[:8]}",
                "description": "Spike test",
            },
            headers={"X-Idempotency-Key": str(uuid.uuid4())},
        )


class MixedUser(HttpUser):
    """
    Realistic user with varied behavior.
    Simulates real-world usage patterns with different operations.
    """

    wait_time = between(2, 5)

    @task(5)
    @tag("payments", "mixed")
    def create_payment(self):
        """Create a payment."""
        response = self.client.post(
            "/payments",
            json={
                "amount": f"{(uuid.uuid4().int % 900) + 100}.00",
                "currency": "USD",
                "state": "AZ",
                "recipient_id": f"user-{uuid.uuid4().hex[:8]}",
                "description": "Mixed test payment",
                "metadata": {"test_id": uuid.uuid4().hex},
            },
            headers={"X-Idempotency-Key": str(uuid.uuid4())},
        )
        if response.status_code == 201:
            self.last_payment_id = response.json().get("payment_id")

    @task(3)
    @tag("payments", "mixed")
    def get_payment(self):
        """Retrieve a previously created payment."""
        payment_id = getattr(self, "last_payment_id", None)
        if payment_id:
            self.client.get(f"/payments/{payment_id}")

    @task(2)
    @tag("payments", "mixed")
    def idempotent_retry(self):
        """Simulate idempotent retry (same request twice)."""
        idempotency_key = str(uuid.uuid4())
        payload = {
            "amount": "75.00",
            "currency": "EUR",
            "state": "WA",
            "recipient_id": f"retry-{uuid.uuid4().hex[:8]}",
            "description": "Idempotent retry test",
        }
        headers = {"X-Idempotency-Key": idempotency_key}
        self.client.post("/payments", json=payload, headers=headers)
        self.client.post("/payments", json=payload, headers=headers)

    @task(1)
    @tag("health", "mixed")
    def health_check(self):
        """Check API health."""
        self.client.get("/health")

    @task(1)
    @tag("errors", "mixed")
    def invalid_payment(self):
        """Test validation error handling."""
        self.client.post(
            "/payments",
            json={
                "amount": "-50.00",
                "currency": "USD",
                "state": "CA",
                "recipient_id": "test",
            },
        )
