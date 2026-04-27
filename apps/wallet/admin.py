from django.contrib import admin

from apps.base.admin import ReadOnlyModelAdmin
from .models import CoinLedgerEntry, CoinPackage, CoinPurchase, CoinSpend


@admin.register(CoinLedgerEntry)
class CoinLedgerEntryAdmin(ReadOnlyModelAdmin):
    list_display = ("id", "user", "entry_type", "amount", "reference_id", "created_at")
    list_filter = ("entry_type", "reference_id")
    search_fields = ("user__email",)
    list_per_page = 100
    list_select_related = ("user",)
    readonly_fields = ("id", "user", "entry_type", "amount", "reference_id", "idempotency_key", "created_at")


@admin.register(CoinPackage)
class CoinPackageAdmin(ReadOnlyModelAdmin):
    list_display = ("id", "name", "coins", "price_cents", "currency", "is_active")
    list_filter = ("is_active", "currency")
    search_fields = ("name",)
    list_per_page = 100
    readonly_fields = ("id", "name", "coins", "price_cents", "currency", "is_active")


@admin.register(CoinPurchase)
class CoinPurchaseAdmin(ReadOnlyModelAdmin):
    list_display = ("id", "user", "package", "coins", "price_cents", "currency", "status", "created_at", "paid_at")
    ordering = ("-created_at",)
    list_filter = ("status", "currency")
    search_fields = ("user__email",)
    list_per_page = 100
    list_select_related = ("user", "package")
    readonly_fields = (
        "id", "user", "package", "coins", "price_cents", "currency",
        "status", "stripe_checkout_session_id", "stripe_payment_intent_id",
        "created_at", "paid_at",
    )


@admin.register(CoinSpend)
class CoinSpendAdmin(ReadOnlyModelAdmin):
    list_display = ("id", "user", "reason", "coins", "target_type", "target_id", "created_at")
    list_filter = ("reason",)
    search_fields = ("user__email",)
    list_per_page = 100
    list_select_related = ("user",)
    readonly_fields = ("id", "user", "reason", "coins", "target_type", "target_id", "created_at")
