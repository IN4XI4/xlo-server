from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.avatar.models import Avatar, UserUnlockedItem, UnlockedItemType, UserUnlockedColor, UserUnlockedSkinColor
from apps.avatar.serializers import AvatarSerializer, AvatarUpdateSerializer, UserUnlockedItemSerializer
from apps.avatar.items.avatar_items import AVATAR_ITEMS
from apps.avatar.items.item_colors import COLORS
from apps.avatar.items.skin_colors import SKIN_COLORS


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
            .only("item_type", "item_code")
            .order_by("item_type", "item_code")
        )

        grouped = {key: [] for key, _ in UnlockedItemType.choices}

        for row in qs:
            meta = AVATAR_ITEMS.get(row.item_type, {}).get(row.item_code)
            if meta:
                grouped[row.item_type].append(
                    {
                        "code": meta["code"],
                        "name": meta["name"],
                        "svg": meta["svg"],
                        "gender": meta["gender"],
                        "id": row.id,
                    }
                )
            else:
                grouped[row.item_type].append({"code": row.item_code})

        return Response(grouped)

    @action(detail=False, methods=["get"], url_path="colors")
    def my_colors(self, request):
        user = request.user
        item_colors_qs = UserUnlockedColor.objects.filter(user=user).only("color_code").order_by("color_code")
        skin_colors_qs = UserUnlockedSkinColor.objects.filter(user=user).only("color_code").order_by("color_code")

        item_colors = [{**COLORS[row.color_code], "code": row.color_code, "id": row.id} for row in item_colors_qs]
        skin_colors = [{**SKIN_COLORS[row.color_code], "code": row.color_code, "id": row.id} for row in skin_colors_qs]

        return Response({"item_colors": item_colors, "skin_colors": skin_colors})
