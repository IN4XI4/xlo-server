from rest_framework import serializers

from apps.avatar.models import Avatar, UserUnlockedItem, UserUnlockedColor, UserUnlockedEyesColor, UserUnlockedSkinColor
from apps.avatar.items.avatar_items import AVATAR_ITEMS
from apps.avatar.items.item_colors import COLORS
from apps.avatar.items.skin_colors import SKIN_COLORS


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

    def _get_item_payload(self, obj, item_type: str, attr: str):
        """
        Devuelve { id, svg } o None si no hay.
        """
        item = getattr(obj, attr)
        if not item:
            return None
        meta = AVATAR_ITEMS.get(item_type, {}).get(item.item_code)
        svg = meta["svg"] if meta else None
        return {"id": item.id, "svg": svg}

    def get_face_item(self, obj):
        return self._get_item_payload(obj, "FACE", "face_item")

    def get_hair_item(self, obj):
        return self._get_item_payload(obj, "HAIR", "hair_item")

    def get_shirt_item(self, obj):
        return self._get_item_payload(obj, "SHIRT", "shirt_item")

    def get_pants_item(self, obj):
        return self._get_item_payload(obj, "PANTS", "pants_item")

    def get_shoes_item(self, obj):
        return self._get_item_payload(obj, "SHOES", "shoes_item")

    def get_accessory_item(self, obj):
        return self._get_item_payload(obj, "ACCESSORY", "accessory_item")

    def get_eyes_color(self, obj):
        # { id, hex }
        return {
            "id": obj.eyes_color_id,
            "hex": COLORS[obj.eyes_color.color_code]["hex"],
        }

    def get_hair_color(self, obj):
        return {
            "id": obj.hair_color_id,
            "hex": COLORS[obj.hair_color.color_code]["hex"],
        }

    def get_shirt_color(self, obj):
        return {
            "id": obj.shirt_color_id,
            "hex": COLORS[obj.shirt_color.color_code]["hex"],
        }

    def get_pants_color(self, obj):
        return {
            "id": obj.pants_color_id,
            "hex": COLORS[obj.pants_color.color_code]["hex"],
        }

    def get_shoes_color(self, obj):
        return {
            "id": obj.shoes_color_id,
            "hex": COLORS[obj.shoes_color.color_code]["hex"],
        }

    def get_accessory_color(self, obj):
        if not obj.accessory_color_id:
            return None
        return {
            "id": obj.accessory_color_id,
            "hex": COLORS[obj.accessory_color.color_code]["hex"],
        }

    def get_skin_color(self, obj):
        sc = SKIN_COLORS[obj.skin_color.color_code]
        return {
            "id": obj.skin_color_id,
            "main_color": sc["main_color"],
            "second_color": sc["second_color"],
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
