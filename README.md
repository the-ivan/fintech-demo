# Fintech Payment API Test Framework Demo

A demonstration test framework for a fintech payment processing API.

## Features
### API
- **Payment Creation**: Process payments with amount, currency, recipient, and description
- **Idempotency**: Prevent duplicate payments with idempotency keys
- **Regulatory Compliance**: State-level restrictions (e.g., NY pending regulatory approval)
- **Validation**: Amount precision, currency support, recipient ID format
- **Error Handling**: Consistent error response format

## Quick Start

```bash
# Install dependencies (includes dev dependencies by default)
uv sync

# Run the server
uv run uvicorn app.main:app --reload

# Run tests
uv run pytest -v
```

API available at `http://localhost:8000` | Docs at `http://localhost:8000/docs` | uv install and docs [here](https://github.com/astral-sh/uv)

## API Usage

### Create Payment

```bash
curl -X POST http://localhost:8000/payments \
  -H "Content-Type: application/json" \
  -H "X-Idempotency-Key: unique-key-123" \
  -d '{
    "amount": "100.00",
    "currency": "USD",
    "state": "CA",
    "recipient_id": "user-123",
    "description": "Payment for services"
  }'
```

### Get Payment

```bash
curl http://localhost:8000/payments/{payment_id}
```

## Testing

```bash
# Run all tests (unit + api)
uv run pytest

# Run only unit tests
uv run pytest tests/unit

# Run only API tests
uv run pytest tests/api

# Run with verbose output
uv run pytest -v

# Run tests in parallel (uses all CPU cores)
uv run pytest -n auto

# Generate HTML report
uv run pytest --html=report.html --self-contained-html
```

## Load Testing

```bash
# Start the API server first
uv run uvicorn app.main:app --reload

# Run Locust web UI (in another terminal)
uv run locust -f tests/performance/locustfile.py --host=http://localhost:8000

# Or run headless (100 users, 10 users/sec spawn rate, 60 seconds)
uv run locust -f tests/performance/locustfile.py --host=http://localhost:8000 \
  --users 100 --spawn-rate 10 --run-time 60s --headless
```

Locust web UI available at `http://localhost:8089`

See [tests/performance/LOAD_TESTING.md](tests/performance/LOAD_TESTING.md) for detailed guides on:
- Load testing (expected traffic)
- Stress testing (find breaking points)
- Spike testing (sudden bursts)
- Soak testing (endurance/memory leaks)
