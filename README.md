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
# Install dependencies
uv sync

# Run the server
uv run uvicorn app.main:app --reload
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

## Restricted States

| State | Reason |
|-------|--------|
| NY    | Pending regulatory approval |

## Project Structure

```
fintech-demo/
├── app/
│   ├── main.py        # FastAPI endpoints
│   └── models.py      # Pydantic models & validators
├── tests/             # Test suite (coming soon)
├── pyproject.toml
└── README.md
```
