import uuid
import pytest
from decimal import Decimal

from django.db import IntegrityError
from django.db.models import ProtectedError

from apps.booking.enums import PaymentKind, PaymentStatus
from apps.booking.models import Payment


@pytest.mark.django_db
class TestPaymentModel:

    def test_creates_payment(self, confirmed_booking):
        payment = Payment.objects.create(
            booking=confirmed_booking,
            kind=PaymentKind.DEPOSIT_HOLD,
            amount=Decimal("600000.00"),
            status=PaymentStatus.PENDING,
        )
        assert payment.pk is not None

    def test_provider_ref_auto_generated(self, confirmed_booking):
        payment = Payment.objects.create(
            booking=confirmed_booking,
            kind=PaymentKind.DEPOSIT_HOLD,
            amount=Decimal("100000.00"),
            status=PaymentStatus.PENDING,
        )
        assert payment.provider_ref is not None
        assert isinstance(payment.provider_ref, uuid.UUID)

    def test_provider_ref_is_unique(self, confirmed_booking):
        ref = uuid.uuid4()
        Payment.objects.create(
            booking=confirmed_booking,
            kind=PaymentKind.DEPOSIT_HOLD,
            amount=Decimal("100000.00"),
            status=PaymentStatus.PENDING,
            provider_ref=ref,
        )
        with pytest.raises(IntegrityError):
            Payment.objects.create(
                booking=confirmed_booking,
                kind=PaymentKind.BALANCE,
                amount=Decimal("200000.00"),
                status=PaymentStatus.PENDING,
                provider_ref=ref,
            )

    def test_booking_protected_from_deletion_while_payment_exists(self, confirmed_booking):
        Payment.objects.create(
            booking=confirmed_booking,
            kind=PaymentKind.DEPOSIT_HOLD,
            amount=Decimal("100000.00"),
            status=PaymentStatus.PENDING,
        )
        with pytest.raises(ProtectedError):
            confirmed_booking.delete()

    def test_created_at_auto_populated(self, confirmed_booking):
        payment = Payment.objects.create(
            booking=confirmed_booking,
            kind=PaymentKind.BALANCE,
            amount=Decimal("100000.00"),
            status=PaymentStatus.COMPLETED,
        )
        assert payment.created_at is not None

    def test_reverse_accessor_from_booking(self, confirmed_booking):
        Payment.objects.create(
            booking=confirmed_booking,
            kind=PaymentKind.DEPOSIT_HOLD,
            amount=Decimal("100000.00"),
            status=PaymentStatus.PENDING,
        )
        assert confirmed_booking.payments.count() == 1
