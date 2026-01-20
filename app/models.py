from datetime import datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field, field_validator


class Currency(str, Enum):
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"


class PaymentStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


# US states where service is unavailable due to regulatory requirements
RESTRICTED_STATES: dict[str, str] = {
    "NY": "Pending regulatory approval.",
}


class PaymentRequest(BaseModel):
    amount: Decimal = Field(..., description="Payment amount", gt=0, le=1000000)
    currency: Currency = Field(default=Currency.USD, description="Three-letter currency code")
    state: str = Field(..., min_length=2, max_length=2, description="US state code")
    recipient_id: str = Field(..., min_length=1, max_length=64, description="Recipient identifier")
    description: str | None = Field(None, max_length=256, description="Payment description")
    idempotency_key: str | None = Field(None, max_length=64, description="Idempotency key")
    metadata: dict[str, str] | None = Field(default_factory=dict, description="Additional metadata")

    @field_validator("amount")
    @classmethod
    def validate_amount_precision(cls, v: Decimal) -> Decimal:
        """Ensure amount has at most 2 decimal places."""
        if v.as_tuple().exponent < -2:
            raise ValueError("Amount cannot have more than 2 decimal places")
        return v

    @field_validator("state")
    @classmethod
    def validate_state(cls, v: str) -> str:
        """Check state against regulatory blacklist."""
        v = v.upper()
        if v in RESTRICTED_STATES:
            reason = RESTRICTED_STATES[v]
            raise ValueError(f"Service unavailable in {v}: {reason}")
        return v

    @field_validator("recipient_id")
    @classmethod
    def validate_recipient_id(cls, v: str) -> str:
        """Validate recipient ID format."""
        if not v.replace("-", "").replace("_", "").isalnum():
            raise ValueError("Recipient ID must be alphanumeric (hyphens and underscores allowed)")
        return v


class PaymentResponse(BaseModel):
    payment_id: str = Field(..., description="Unique payment identifier")
    status: PaymentStatus = Field(..., description="Current payment status")
    amount: Decimal = Field(..., description="Payment amount")
    currency: Currency = Field(..., description="Payment currency")
    state: str = Field(..., description="US state code")
    recipient_id: str = Field(..., description="Recipient identifier")
    description: str | None = Field(None, description="Payment description")
    idempotency_key: str | None = Field(None, description="Idempotency key if provided")
    created_at: datetime = Field(..., description="Timestamp of payment creation")
    metadata: dict[str, str] = Field(default_factory=dict, description="Additional metadata")


class ErrorResponse(BaseModel):
    error_code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error message")
    details: dict | None = Field(None, description="Additional error details")
