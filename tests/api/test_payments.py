

class TestHealthCheck:
    async def test_health_returns_healthy(self, client):
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data


class TestCreatePayment:
    async def test_create_payment_success(self, client, valid_payment_data):
        response = await client.post("/payments", json=valid_payment_data)
        assert response.status_code == 201
        data = response.json()
        assert data["amount"] == "100.00"
        assert data["currency"] == "USD"
        assert data["state"] == "CA"
        assert data["recipient_id"] == "user-123"
        assert data["status"] == "pending"
        assert "payment_id" in data
        assert "created_at" in data

    async def test_create_payment_minimal(self, client):
        response = await client.post("/payments", json={
            "amount": "50.00",
            "state": "TX",
            "recipient_id": "user-456",
        })
        assert response.status_code == 201
        assert response.json()["currency"] == "USD"  # default

    async def test_create_payment_with_metadata(self, client, valid_payment_data):
        valid_payment_data["metadata"] = {"order_id": "ORD-123"}
        response = await client.post("/payments", json=valid_payment_data)
        assert response.status_code == 201
        assert response.json()["metadata"] == {"order_id": "ORD-123"}


class TestIdempotency:
    async def test_idempotent_request_returns_same_payment(self, client, valid_payment_data):
        headers = {"X-Idempotency-Key": "test-key-001"}

        response1 = await client.post("/payments", json=valid_payment_data, headers=headers)
        response2 = await client.post("/payments", json=valid_payment_data, headers=headers)

        assert response1.status_code == 201
        assert response2.status_code == 201
        assert response1.json()["payment_id"] == response2.json()["payment_id"]

    async def test_idempotency_conflict_different_amount(self, client, valid_payment_data):
        headers = {"X-Idempotency-Key": "test-key-002"}

        await client.post("/payments", json=valid_payment_data, headers=headers)

        valid_payment_data["amount"] = "200.00"
        response = await client.post("/payments", json=valid_payment_data, headers=headers)

        assert response.status_code == 409
        assert response.json()["detail"]["error_code"] == "IDEMPOTENCY_CONFLICT"

    async def test_idempotency_conflict_different_recipient(self, client, valid_payment_data):
        headers = {"X-Idempotency-Key": "test-key-003"}

        await client.post("/payments", json=valid_payment_data, headers=headers)

        valid_payment_data["recipient_id"] = "different-user"
        response = await client.post("/payments", json=valid_payment_data, headers=headers)

        assert response.status_code == 409


class TestGetPayment:
    async def test_get_payment_success(self, client, valid_payment_data):
        create_response = await client.post("/payments", json=valid_payment_data)
        payment_id = create_response.json()["payment_id"]

        response = await client.get(f"/payments/{payment_id}")
        assert response.status_code == 200
        assert response.json()["payment_id"] == payment_id

    async def test_get_payment_not_found(self, client):
        response = await client.get("/payments/nonexistent-id")
        assert response.status_code == 404
        assert response.json()["detail"]["error_code"] == "NOT_FOUND"


class TestValidation:
    async def test_restricted_state_ny(self, client, valid_payment_data):
        valid_payment_data["state"] = "NY"
        response = await client.post("/payments", json=valid_payment_data)
        assert response.status_code == 422
        assert "regulatory approval" in str(response.json()).lower()

    async def test_invalid_amount_negative(self, client, valid_payment_data):
        valid_payment_data["amount"] = "-10.00"
        response = await client.post("/payments", json=valid_payment_data)
        assert response.status_code == 422

    async def test_invalid_amount_too_many_decimals(self, client, valid_payment_data):
        valid_payment_data["amount"] = "10.001"
        response = await client.post("/payments", json=valid_payment_data)
        assert response.status_code == 422

    async def test_invalid_amount_exceeds_max(self, client, valid_payment_data):
        valid_payment_data["amount"] = "1000001.00"
        response = await client.post("/payments", json=valid_payment_data)
        assert response.status_code == 422

    async def test_invalid_currency(self, client, valid_payment_data):
        valid_payment_data["currency"] = "BTC"
        response = await client.post("/payments", json=valid_payment_data)
        assert response.status_code == 422

    async def test_invalid_recipient_id_special_chars(self, client, valid_payment_data):
        valid_payment_data["recipient_id"] = "user@123!"
        response = await client.post("/payments", json=valid_payment_data)
        assert response.status_code == 422

    async def test_missing_required_fields(self, client):
        response = await client.post("/payments", json={})
        assert response.status_code == 422
