from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.models import Currency, PaymentRequest


class TestPaymentRequestValidation:
    def test_valid_payment_request(self):
        payment = PaymentRequest(
            amount=Decimal("100.00"),
            currency=Currency.USD,
            state="CA",
            recipient_id="user-123",
        )
        assert payment.amount == Decimal("100.00")
        assert payment.state == "CA"

    def test_state_uppercase_conversion(self):
        payment = PaymentRequest(
            amount=Decimal("100.00"),
            state="ca",
            recipient_id="user-123",
        )
        assert payment.state == "CA"

    def test_restricted_state_ny_raises_error(self):
        with pytest.raises(ValidationError) as exc_info:
            PaymentRequest(
                amount=Decimal("100.00"),
                state="NY",
                recipient_id="user-123",
            )
        assert "Service unavailable in NY" in str(exc_info.value)

    def test_amount_precision_valid(self):
        payment = PaymentRequest(
            amount=Decimal("99.99"),
            state="CA",
            recipient_id="user-123",
        )
        assert payment.amount == Decimal("99.99")

    def test_amount_precision_invalid(self):
        with pytest.raises(ValidationError) as exc_info:
            PaymentRequest(
                amount=Decimal("99.999"),
                state="CA",
                recipient_id="user-123",
            )
        assert "decimal places" in str(exc_info.value).lower()

    def test_recipient_id_with_hyphen(self):
        payment = PaymentRequest(
            amount=Decimal("100.00"),
            state="CA",
            recipient_id="user-123-abc",
        )
        assert payment.recipient_id == "user-123-abc"

    def test_recipient_id_with_underscore(self):
        payment = PaymentRequest(
            amount=Decimal("100.00"),
            state="CA",
            recipient_id="user_123",
        )
        assert payment.recipient_id == "user_123"

    def test_recipient_id_invalid_chars(self):
        with pytest.raises(ValidationError):
            PaymentRequest(
                amount=Decimal("100.00"),
                state="CA",
                recipient_id="user@123",
            )
