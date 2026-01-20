import uuid
from datetime import UTC, datetime

from fastapi import FastAPI, Header, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.models import (
    ErrorResponse,
    PaymentRequest,
    PaymentResponse,
    PaymentStatus,
)

app = FastAPI(
    title="Fintech Payment API",
    description="Demo payment processing API with idempotency and regulatory compliance",
    version="0.1.0",
)

# In-memory storage for demo purposes
payments_db: dict[str, PaymentResponse] = {}
idempotency_store: dict[str, str] = {}  # idempotency_key -> payment_id


@app.exception_handler(ValidationError)
async def validation_exception_handler(request, exc: ValidationError):
    """Handle Pydantic validation errors."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse(
            error_code="VALIDATION_ERROR",
            message="Request validation failed",
            details={"errors": exc.errors()},
        ).model_dump(),
    )


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now(UTC).isoformat()}


@app.post(
    "/payments",
    response_model=PaymentResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        409: {"model": ErrorResponse, "description": "Idempotency conflict"},
        422: {"model": ErrorResponse, "description": "Validation error"},
    },
)
async def create_payment(
    payment_request: PaymentRequest,
    x_idempotency_key: str | None = Header(None, alias="X-Idempotency-Key"),
) -> PaymentResponse:
    """
    Create a new payment.

    - Idempotency via X-Idempotency-Key header
    - State-level regulatory restrictions (e.g., NY unavailable)
    - Amount and currency validation
    """
    idempotency_key = x_idempotency_key or payment_request.idempotency_key

    # Handle idempotent requests
    if idempotency_key and idempotency_key in idempotency_store:
        existing_payment = payments_db.get(idempotency_store[idempotency_key])
        if existing_payment:
            # Verify request matches original
            if (
                existing_payment.amount != payment_request.amount
                or existing_payment.currency != payment_request.currency
                or existing_payment.recipient_id != payment_request.recipient_id
            ):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={
                        "error_code": "IDEMPOTENCY_CONFLICT",
                        "message": "Idempotency key already used with different parameters",
                    },
                )
            return existing_payment

    # Create payment
    payment_id = str(uuid.uuid4())
    payment = PaymentResponse(
        payment_id=payment_id,
        status=PaymentStatus.PENDING,
        amount=payment_request.amount,
        currency=payment_request.currency,
        state=payment_request.state,
        recipient_id=payment_request.recipient_id,
        description=payment_request.description,
        idempotency_key=idempotency_key,
        created_at=datetime.now(UTC),
        metadata=payment_request.metadata or {},
    )

    payments_db[payment_id] = payment
    if idempotency_key:
        idempotency_store[idempotency_key] = payment_id

    return payment


@app.get(
    "/payments/{payment_id}",
    response_model=PaymentResponse,
    responses={404: {"model": ErrorResponse}},
)
async def get_payment(payment_id: str) -> PaymentResponse:
    """Retrieve a payment by ID."""
    if payment_id not in payments_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "NOT_FOUND", "message": "Payment not found"},
        )
    return payments_db[payment_id]
