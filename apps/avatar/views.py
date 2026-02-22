from django.db import transaction
from django.db.models import Exists, OuterRef, Subquery

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.avatar.models import (
    Avatar,
    AvatarColorCatalog,
    AvatarItemCatalog,
    AvatarSkinColorCatalog,
    UserUnlockedColor,
    UserUnlockedItem,
    UserUnlockedSkinColor,
    UnlockedItemType,
)
from rest_framework.pagination import PageNumberPagination

from apps.avatar.serializers import (
    AvatarSerializer,
    AvatarUpdateSerializer,
    AvatarColorCatalogSerializer,
    AvatarItemCatalogSerializer,
    AvatarSkinColorCatalogSerializer,
    UserUnlockedColorSerializer,
    UserUnlockedItemSerializer,
    UserUnlockedSkinColorSerializer,
)
from apps.users.models import CustomUser
from apps.wallet.models import CoinSpend


class CatalogPagination(PageNumberPagination):
    page_size = 20


class AvatarViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]  # TODO: Fix permissions to only allow owner
    queryset = Avatar.objects.all()
    filterset_fields = {
        "user__id": ("exact",),
    }

    def get_serializer_class(self):
        if self.action in ["update", "partial_update"]:
            return AvatarUpdateSerializer
        return AvatarSerializer

    def perform_update(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=["get"], url_path="my-avatar")
    def get_my_avatar(self, request):
        try:
            avatar = Avatar.objects.get(user=request.user)
        except Avatar.DoesNotExist:
            return Response({"detail": "Avatar not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(avatar)
        return Response(serializer.data)


class UserUnlockedItemViewSet(viewsets.ReadOnlyModelViewSet):

    permission_classes = [IsAuthenticated]  # TODO: Fix permissions to only allow owner
    serializer_class = UserUnlockedItemSerializer
    filterset_fields = {
        "item_type": ("exact",),
        "item_code": ("icontains",),
    }

    def get_queryset(self):
        user = self.request.user
        qs = UserUnlockedItem.objects.all()
        if user.is_superuser:
            return qs
        return qs.filter(user=user)

    @action(detail=False, methods=["get"], url_path="grouped")
    def my_grouped(self, request):
        qs = (
            UserUnlockedItem.objects.filter(user=request.user)
            .select_related("catalog_item")
            .order_by("catalog_item__item_type", "catalog_item__code")
        )

        grouped = {key: [] for key, _ in UnlockedItemType.choices}

        for row in qs:
            item = row.catalog_item
            grouped[item.item_type].append(
                {
                    "code": item.code,
                    "name": item.name,
                    "svg": item.svg,
                    "gender": item.avatar_type,
                    "id": row.id,
                }
            )

        return Response(grouped)

    @action(detail=False, methods=["get"], url_path="defaults")
    def defaults(self, request):
        avatar_type = request.query_params.get("avatar_type")
        if not avatar_type:
            return Response({"detail": "avatar_type is required."}, status=status.HTTP_400_BAD_REQUEST)

        qs = (
            UserUnlockedItem.objects.filter(
                user=request.user,
                catalog_item__avatar_type=avatar_type,
            )
            .exclude(catalog_item__item_type=UnlockedItemType.ACCESSORY)
            .select_related("catalog_item")
            .order_by("catalog_item__item_type", "id")
            .distinct("catalog_item__item_type")
        )

        defaults = {
            row.catalog_item.item_type: {
                "unlocked_item_id": row.id,
                "code": row.catalog_item.code,
                "name": row.catalog_item.name,
                "svg": row.catalog_item.svg,
            }
            for row in qs
        }

        return Response(defaults)

    @action(detail=False, methods=["get"], url_path="store")
    def store(self, request):
        # TODO: this endpoint is not being used right now.
        owned_ids = UserUnlockedItem.objects.filter(user=request.user).values_list("catalog_item_id", flat=True)
        qs = AvatarItemCatalog.objects.filter(is_active=True).exclude(id__in=owned_ids).order_by("item_type", "code")

        item_type = request.query_params.get("item_type")
        if item_type:
            qs = qs.filter(item_type=item_type)

        page = self.paginate_queryset(qs)
        data = [
            {
                "id": item.id,
                "code": item.code,
                "name": item.name,
                "svg": item.svg,
                "item_type": item.item_type,
                "gender": item.avatar_type,
                "price": item.price,
            }
            for item in page
        ]
        return self.get_paginated_response(data)

    @action(detail=False, methods=["post"], url_path="buy-item")
    def buy_item(self, request):
        catalog_item_id = request.data.get("catalog_item_id")
        if not catalog_item_id:
            return Response({"detail": "catalog_item_id is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            catalog_item = AvatarItemCatalog.objects.get(id=catalog_item_id, is_active=True)
        except AvatarItemCatalog.DoesNotExist:
            return Response({"detail": "Item not found."}, status=status.HTTP_404_NOT_FOUND)

        with transaction.atomic():
            user = CustomUser.objects.select_for_update().get(pk=request.user.pk)

            if UserUnlockedItem.objects.filter(user=user, catalog_item=catalog_item).exists():
                return Response({"detail": "Item already owned."}, status=status.HTTP_409_CONFLICT)

            if user.coin_balance < catalog_item.price:
                return Response(
                    {"detail": "Insufficient coins.", "code": "insufficient_coins"},
                    status=status.HTTP_402_PAYMENT_REQUIRED,
                )

            unlocked_item = UserUnlockedItem.objects.create(user=user, catalog_item=catalog_item)
            CoinSpend.objects.create(
                user=user,
                reason=CoinSpend.Reason.BUY_ITEM,
                coins=catalog_item.price,
                target_type="avatar_item",
                target_id=str(catalog_item.id),
            )
            user.coin_balance -= catalog_item.price
            user.save(update_fields=["coin_balance"])

        return Response(
            {"unlocked_item_id": unlocked_item.id, "coin_balance": user.coin_balance},
            status=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=["get"], url_path="colors")
    def my_colors(self, request):
        user = request.user
        item_colors_qs = (
            UserUnlockedColor.objects.filter(user=user).select_related("catalog_item").order_by("catalog_item__code")
        )
        skin_colors_qs = (
            UserUnlockedSkinColor.objects.filter(user=user)
            .select_related("catalog_item")
            .order_by("catalog_item__code")
        )

        item_colors = [
            {"code": row.catalog_item.code, "name": row.catalog_item.name, "hex": row.catalog_item.hex, "id": row.id}
            for row in item_colors_qs
        ]
        skin_colors = [
            {
                "code": row.catalog_item.code,
                "name": row.catalog_item.name,
                "main_color": row.catalog_item.main_color,
                "second_color": row.catalog_item.second_color,
                "id": row.id,
            }
            for row in skin_colors_qs
        ]

        return Response({"item_colors": item_colors, "skin_colors": skin_colors})


class AvatarItemCatalogViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = AvatarItemCatalogSerializer
    pagination_class = CatalogPagination
    filterset_fields = {
        "item_type": ("exact",),
        "avatar_type": ("exact",),
    }

    def get_queryset(self):
        user_items = UserUnlockedItem.objects.filter(
            user=self.request.user,
            catalog_item=OuterRef("pk"),
        )
        return (
            AvatarItemCatalog.objects.filter(is_active=True)
            .annotate(
                owned=Exists(user_items),
                unlocked_item_id=Subquery(user_items.values("id")[:1]),
            )
            .order_by("-owned", "name")
        )


class UserUnlockedColorViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = UserUnlockedColorSerializer

    def get_queryset(self):
        user = self.request.user
        qs = UserUnlockedColor.objects.all()
        if user.is_superuser:
            return qs
        return qs.filter(user=user)

    @action(detail=False, methods=["post"], url_path="buy-color")
    def buy_color(self, request):
        catalog_item_id = request.data.get("catalog_item_id")
        if not catalog_item_id:
            return Response({"detail": "catalog_item_id is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            catalog_item = AvatarColorCatalog.objects.get(id=catalog_item_id, is_active=True)
        except AvatarColorCatalog.DoesNotExist:
            return Response({"detail": "Color not found."}, status=status.HTTP_404_NOT_FOUND)

        with transaction.atomic():
            user = CustomUser.objects.select_for_update().get(pk=request.user.pk)

            if UserUnlockedColor.objects.filter(user=user, catalog_item=catalog_item).exists():
                return Response({"detail": "Color already owned."}, status=status.HTTP_409_CONFLICT)

            if user.coin_balance < catalog_item.price:
                return Response(
                    {"detail": "Insufficient coins.", "code": "insufficient_coins"},
                    status=status.HTTP_402_PAYMENT_REQUIRED,
                )

            unlocked_color = UserUnlockedColor.objects.create(user=user, catalog_item=catalog_item)
            CoinSpend.objects.create(
                user=user,
                reason=CoinSpend.Reason.BUY_COLOR,
                coins=catalog_item.price,
                target_type="item_color",
                target_id=str(catalog_item.id),
            )
            user.coin_balance -= catalog_item.price
            user.save(update_fields=["coin_balance"])

        return Response(
            {"unlocked_color_id": unlocked_color.id, "coin_balance": user.coin_balance},
            status=status.HTTP_201_CREATED,
        )


class UserUnlockedSkinColorViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = UserUnlockedSkinColorSerializer

    def get_queryset(self):
        user = self.request.user
        qs = UserUnlockedSkinColor.objects.all()
        if user.is_superuser:
            return qs
        return qs.filter(user=user)

    @action(detail=False, methods=["post"], url_path="buy-color")
    def buy_color(self, request):
        catalog_item_id = request.data.get("catalog_item_id")
        if not catalog_item_id:
            return Response({"detail": "catalog_item_id is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            catalog_item = AvatarSkinColorCatalog.objects.get(id=catalog_item_id, is_active=True)
        except AvatarSkinColorCatalog.DoesNotExist:
            return Response({"detail": "Skin color not found."}, status=status.HTTP_404_NOT_FOUND)

        with transaction.atomic():
            user = CustomUser.objects.select_for_update().get(pk=request.user.pk)

            if UserUnlockedSkinColor.objects.filter(user=user, catalog_item=catalog_item).exists():
                return Response({"detail": "Skin color already owned."}, status=status.HTTP_409_CONFLICT)

            if user.coin_balance < catalog_item.price:
                return Response(
                    {"detail": "Insufficient coins.", "code": "insufficient_coins"},
                    status=status.HTTP_402_PAYMENT_REQUIRED,
                )

            unlocked_skin_color = UserUnlockedSkinColor.objects.create(user=user, catalog_item=catalog_item)
            CoinSpend.objects.create(
                user=user,
                reason=CoinSpend.Reason.BUY_COLOR,
                coins=catalog_item.price,
                target_type="skin_color",
                target_id=str(catalog_item.id),
            )
            user.coin_balance -= catalog_item.price
            user.save(update_fields=["coin_balance"])

        return Response(
            {"unlocked_skin_color_id": unlocked_skin_color.id, "coin_balance": user.coin_balance},
            status=status.HTTP_201_CREATED,
        )


class AvatarColorCatalogViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = AvatarColorCatalogSerializer
    pagination_class = CatalogPagination

    def get_queryset(self):
        user_colors = UserUnlockedColor.objects.filter(
            user=self.request.user,
            catalog_item=OuterRef("pk"),
        )
        return (
            AvatarColorCatalog.objects.filter(is_active=True)
            .annotate(
                owned=Exists(user_colors),
                unlocked_item_id=Subquery(user_colors.values("id")[:1]),
            )
            .order_by("-owned", "code")
        )


class AvatarSkinColorCatalogViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = AvatarSkinColorCatalogSerializer
    pagination_class = CatalogPagination

    def get_queryset(self):
        user_skin_colors = UserUnlockedSkinColor.objects.filter(
            user=self.request.user,
            catalog_item=OuterRef("pk"),
        )
        return (
            AvatarSkinColorCatalog.objects.filter(is_active=True)
            .annotate(
                owned=Exists(user_skin_colors),
                unlocked_item_id=Subquery(user_skin_colors.values("id")[:1]),
            )
            .order_by("-owned", "code")
        )
