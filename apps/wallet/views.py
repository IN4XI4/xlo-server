import stripe
from django.conf import settings
from django.db import transaction
from django.db.models import F
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.avatar.models import AvatarColorCatalog, AvatarItemCatalog, AvatarSkinColorCatalog
from apps.base.views import StandardPagination
from apps.blog.models import Notification
from .models import CoinLedgerEntry, CoinPackage, CoinPurchase, CoinSpend
from .serializers import CoinPackageSerializer, LedgerEntrySerializer

stripe.api_key = settings.STRIPE_SECRET_KEY


class CoinPackageListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        packages = CoinPackage.objects.filter(is_active=True).order_by("price_cents")
        serializer = CoinPackageSerializer(packages, many=True)
        return Response(serializer.data)


class CreateCheckoutSessionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, package_id):
        try:
            package = CoinPackage.objects.get(id=package_id, is_active=True)
        except CoinPackage.DoesNotExist:
            return Response({"detail": "Package not found."}, status=status.HTTP_404_NOT_FOUND)

        purchase = CoinPurchase.objects.create(
            user=request.user,
            package=package,
            coins=package.coins,
            price_cents=package.price_cents,
            currency=package.currency,
            status=CoinPurchase.Status.PENDING,
        )

        try:
            session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[
                    {
                        "price_data": {
                            "currency": package.currency.lower(),
                            "product_data": {"name": package.name},
                            "unit_amount": package.price_cents,
                        },
                        "quantity": 1,
                    }
                ],
                mode="payment",
                metadata={"purchase_id": str(purchase.id)},
                success_url=request.data.get("success_url", ""),
                cancel_url=request.data.get("cancel_url", ""),
            )
        except stripe.error.StripeError as e:
            purchase.status = CoinPurchase.Status.FAILED
            purchase.save(update_fields=["status"])
            return Response({"detail": str(e)}, status=status.HTTP_502_BAD_GATEWAY)

        purchase.stripe_checkout_session_id = session.id
        purchase.save(update_fields=["stripe_checkout_session_id"])

        Notification.objects.create(
            user=request.user,
            notification_type=Notification.Type.COIN_PURCHASE_PENDING,
            metadata={"coins": package.coins, "price_cents": package.price_cents, "currency": package.currency},
        )

        return Response({"checkout_url": session.url, "purchase_id": str(purchase.id)})


class CoinLedgerHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = CoinLedgerEntry.objects.filter(user=request.user).order_by("-created_at")
        paginator = StandardPagination()
        entries = paginator.paginate_queryset(qs, request, view=self)

        purchase_ids = set()
        spend_ids = set()
        for entry in entries:
            if entry.reference_id.startswith("purchase:"):
                purchase_ids.add(entry.reference_id.split(":", 1)[1])
            elif entry.reference_id.startswith("spend:"):
                try:
                    spend_ids.add(int(entry.reference_id.split(":", 1)[1]))
                except ValueError:
                    pass

        avatar_item_ids = set()
        item_color_ids = set()
        skin_color_ids = set()

        purchases = {str(p.id): p for p in CoinPurchase.objects.filter(id__in=purchase_ids).select_related("package")}
        spends = {s.id: s for s in CoinSpend.objects.filter(id__in=spend_ids)}

        for spend in spends.values():
            if spend.reason == CoinSpend.Reason.BUY_ITEM and spend.target_type == "avatar_item":
                avatar_item_ids.add(int(spend.target_id))
            elif spend.reason == CoinSpend.Reason.BUY_COLOR:
                if spend.target_type == "item_color":
                    item_color_ids.add(int(spend.target_id))
                elif spend.target_type == "skin_color":
                    skin_color_ids.add(int(spend.target_id))

        avatar_items = {i.id: i for i in AvatarItemCatalog.objects.filter(id__in=avatar_item_ids)}
        item_colors = {c.id: c for c in AvatarColorCatalog.objects.filter(id__in=item_color_ids)}
        skin_colors = {c.id: c for c in AvatarSkinColorCatalog.objects.filter(id__in=skin_color_ids)}

        serializer = LedgerEntrySerializer(
            entries,
            many=True,
            context={
                "purchases": purchases,
                "spends": spends,
                "avatar_items": avatar_items,
                "item_colors": item_colors,
                "skin_colors": skin_colors,
            },
        )
        return paginator.get_paginated_response(serializer.data)


@csrf_exempt
def stripe_webhook(request):
    from django.http import HttpResponse
    from apps.users.models import CustomUser

    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE", "")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)
    except (ValueError, stripe.error.SignatureVerificationError):
        return HttpResponse(status=400)

    if event["type"] == "checkout.session.completed":
        session = event.to_dict()["data"]["object"]
        purchase_id = session.get("metadata", {}).get("purchase_id")

        if not purchase_id:
            return HttpResponse(status=400)

        idempotency_key = f"purchase:{purchase_id}"

        with transaction.atomic():
            try:
                purchase = CoinPurchase.objects.select_related("user").select_for_update().get(id=purchase_id)
            except CoinPurchase.DoesNotExist:
                return HttpResponse(status=404)

            if purchase.status == CoinPurchase.Status.PAID:
                return HttpResponse(status=200)

            purchase.status = CoinPurchase.Status.PAID
            purchase.paid_at = timezone.now()
            purchase.stripe_payment_intent_id = session.get("payment_intent")
            purchase.save(update_fields=["status", "paid_at", "stripe_payment_intent_id"])

            CoinLedgerEntry.objects.get_or_create(
                idempotency_key=idempotency_key,
                defaults={
                    "user": purchase.user,
                    "entry_type": CoinLedgerEntry.Type.CREDIT,
                    "amount": purchase.coins,
                    "reference_id": f"purchase:{purchase_id}",
                },
            )

            CustomUser.objects.filter(pk=purchase.user_id).update(coin_balance=F("coin_balance") + purchase.coins)

            Notification.objects.create(
                user=purchase.user,
                notification_type=Notification.Type.COIN_PURCHASE_SUCCESS,
                metadata={"coins": purchase.coins, "price_cents": purchase.price_cents, "currency": purchase.currency},
            )

    return HttpResponse(status=200)
