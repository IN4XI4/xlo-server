import uuid

from django.db import models
from django.core.validators import MinValueValidator

from apps.users.models import CustomUser


class CoinPackage(models.Model):
    name = models.CharField(max_length=80)
    coins = models.PositiveIntegerField()
    price_cents = models.PositiveIntegerField()
    currency = models.CharField(max_length=10, default="EUR")
    is_active = models.BooleanField(default=True)


class CoinLedgerEntry(models.Model):
    class Type(models.TextChoices):
        CREDIT = "credit"
        DEBIT = "debit"

    user = models.ForeignKey(CustomUser, on_delete=models.PROTECT, related_name="coin_ledger_entries")
    entry_type = models.CharField(max_length=20, choices=Type.choices)
    amount = models.BigIntegerField(validators=[MinValueValidator(1)])
    created_at = models.DateTimeField(auto_now_add=True)
    reference_id = models.CharField(max_length=100)

    idempotency_key = models.CharField(max_length=120, unique=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "-created_at"]),
        ]


class CoinPurchase(models.Model):
    class Status(models.TextChoices):
        CREATED = "created"
        PENDING = "pending"
        PAID = "paid"
        FAILED = "failed"
        CANCELED = "canceled"
        REFUNDED = "refunded"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(CustomUser, on_delete=models.PROTECT, related_name="coin_purchases")
    package = models.ForeignKey(CoinPackage, on_delete=models.PROTECT)
    coins = models.PositiveIntegerField()
    price_cents = models.PositiveIntegerField()
    currency = models.CharField(max_length=10, default="EUR")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.CREATED)

    # Stripe
    stripe_checkout_session_id = models.CharField(max_length=255, blank=True, null=True, unique=True)
    stripe_payment_intent_id = models.CharField(max_length=255, blank=True, null=True, unique=True)

    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["status", "-created_at"]),
        ]


class CoinSpend(models.Model):
    class Reason(models.TextChoices):
        BUY_ITEM = "buy_item"
        BUY_COLOR = "buy_color"
        PRIVATE_SPACE = "private_space"

    user = models.ForeignKey(CustomUser, on_delete=models.PROTECT, related_name="coin_spends")
    reason = models.CharField(max_length=30, choices=Reason.choices)
    coins = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    target_type = models.CharField(max_length=50, blank=True, default="")
    target_id = models.CharField(max_length=100, blank=True, default="")
