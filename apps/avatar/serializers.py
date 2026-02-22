from rest_framework import serializers

from apps.avatar.models import (
    Avatar,
    AvatarColorCatalog,
    AvatarItemCatalog,
    AvatarSkinColorCatalog,
    UserUnlockedItem,
    UserUnlockedColor,
    UserUnlockedEyesColor,
    UserUnlockedSkinColor,
)
from apps.avatar.items.item_colors import COLORS


class AvatarSerializer(serializers.ModelSerializer):
    face_item = serializers.SerializerMethodField()
    hair_item = serializers.SerializerMethodField()
    shirt_item = serializers.SerializerMethodField()
    pants_item = serializers.SerializerMethodField()
    shoes_item = serializers.SerializerMethodField()
    accessory_item = serializers.SerializerMethodField()

    eyes_color = serializers.SerializerMethodField()
    hair_color = serializers.SerializerMethodField()
    shirt_color = serializers.SerializerMethodField()
    pants_color = serializers.SerializerMethodField()
    shoes_color = serializers.SerializerMethodField()
    accessory_color = serializers.SerializerMethodField()
    skin_color = serializers.SerializerMethodField()

    class Meta:
        model = Avatar
        fields = "__all__"
        read_only_fields = ["user"]

    def _get_item_payload(self, obj, attr: str):
        """
        Devuelve { id, svg } o None si no hay.
        """
        item = getattr(obj, attr)
        if not item:
            return None
        return {"id": item.id, "svg": item.catalog_item.svg}

    def get_face_item(self, obj):
        return self._get_item_payload(obj, "face_item")

    def get_hair_item(self, obj):
        return self._get_item_payload(obj, "hair_item")

    def get_shirt_item(self, obj):
        return self._get_item_payload(obj, "shirt_item")

    def get_pants_item(self, obj):
        return self._get_item_payload(obj, "pants_item")

    def get_shoes_item(self, obj):
        return self._get_item_payload(obj, "shoes_item")

    def get_accessory_item(self, obj):
        return self._get_item_payload(obj, "accessory_item")

    def _get_color_payload(self, obj, attr: str):
        color = getattr(obj, attr)
        if not color:
            return None
        return {"id": color.id, "hex": color.catalog_item.hex}

    def get_eyes_color(self, obj):
        return {
            "id": obj.eyes_color_id,
            "hex": COLORS[obj.eyes_color.color_code]["hex"],
        }

    def get_hair_color(self, obj):
        return self._get_color_payload(obj, "hair_color")

    def get_shirt_color(self, obj):
        return self._get_color_payload(obj, "shirt_color")

    def get_pants_color(self, obj):
        return self._get_color_payload(obj, "pants_color")

    def get_shoes_color(self, obj):
        return self._get_color_payload(obj, "shoes_color")

    def get_accessory_color(self, obj):
        return self._get_color_payload(obj, "accessory_color")

    def get_skin_color(self, obj):
        return {
            "id": obj.skin_color_id,
            "main_color": obj.skin_color.catalog_item.main_color,
            "second_color": obj.skin_color.catalog_item.second_color,
        }


class AvatarUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Avatar
        fields = [
            "avatar_type",
            "hair_item",
            "hair_color",
            "face_item",
            "eyes_color",
            "shirt_item",
            "shirt_color",
            "pants_item",
            "pants_color",
            "shoes_item",
            "shoes_color",
            "accessory_item",
            "accessory_color",
            "skin_color",
        ]
        read_only_fields = ["user"]


class UserUnlockedItemSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserUnlockedItem
        fields = "__all__"


class UserUnlockedColorSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserUnlockedColor
        fields = "__all__"


class UserUnlockedSkinColorSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserUnlockedSkinColor
        fields = "__all__"


class UserUnlockedEyesColorSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserUnlockedEyesColor
        fields = "__all__"


class AvatarItemCatalogSerializer(serializers.ModelSerializer):
    owned = serializers.BooleanField(read_only=True)
    gender = serializers.CharField(source="avatar_type", read_only=True)
    unlocked_item_id = serializers.IntegerField(read_only=True, allow_null=True)

    class Meta:
        model = AvatarItemCatalog
        fields = ["id", "code", "name", "svg", "item_type", "gender", "price", "owned", "unlocked_item_id"]


class AvatarColorCatalogSerializer(serializers.ModelSerializer):
    owned = serializers.BooleanField(read_only=True)
    unlocked_item_id = serializers.IntegerField(read_only=True, allow_null=True)

    class Meta:
        model = AvatarColorCatalog
        fields = ["id", "code", "name", "hex", "price", "owned", "unlocked_item_id"]


class AvatarSkinColorCatalogSerializer(serializers.ModelSerializer):
    owned = serializers.BooleanField(read_only=True)
    unlocked_item_id = serializers.IntegerField(read_only=True, allow_null=True)

    class Meta:
        model = AvatarSkinColorCatalog
        fields = ["id", "code", "name", "main_color", "second_color", "price", "owned", "unlocked_item_id"]
