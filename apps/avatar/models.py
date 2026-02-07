from django.db import models

from apps.users.models import CustomUser


class UnlockedItemType(models.TextChoices):
    FACE = "FACE", "Face"
    HAIR = "HAIR", "Hair"
    SHIRT = "SHIRT", "Shirt"
    PANTS = "PANTS", "Pants"
    SHOES = "SHOES", "Shoes"
    ACCESSORY = "ACCESSORY", "Accessory"


class AvatarType(models.TextChoices):
    BOY = "BOY", "Boy"
    GIRL = "GIRL", "Girl"


class BaseCatalog(models.Model):
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    price = models.PositiveIntegerField(default=0)

    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ["sort_order", "code"]

    def __str__(self):
        return self.code


class AvatarColorCatalog(BaseCatalog):
    hex = models.CharField(max_length=7)


class AvatarSkinColorCatalog(BaseCatalog):
    main_color = models.CharField(max_length=7)
    second_color = models.CharField(max_length=7)


class AvatarItemCatalog(BaseCatalog):
    item_type = models.CharField(max_length=20, choices=UnlockedItemType.choices)
    avatar_type = models.CharField(max_length=20, choices=AvatarType.choices)
    svg = models.CharField(max_length=200)

    class Meta(BaseCatalog.Meta):
        indexes = [
            models.Index(fields=["item_type", "avatar_type", "is_active"]),
        ]


class UserUnlockedItem(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="unlocked_items")
    catalog_item = models.ForeignKey(AvatarItemCatalog, on_delete=models.PROTECT, related_name="unlocks")
    unlocked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "catalog_item")

    def __str__(self):
        return f"{self.item_code}"


class UserUnlockedColor(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="unlocked_colors")
    catalog_item = models.ForeignKey(AvatarColorCatalog, on_delete=models.PROTECT, related_name="unlocks")
    unlocked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "catalog_item")

    def __str__(self):
        return f"{self.color_code}"


class UserUnlockedSkinColor(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="unlocked_skin_colors")
    catalog_item = models.ForeignKey(AvatarSkinColorCatalog, on_delete=models.PROTECT, related_name="unlocks")
    unlocked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "catalog_item")

    def __str__(self):
        return f"{self.color_code}"


class UserUnlockedEyesColor(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="unlocked_eyes_colors")
    color_code = models.CharField(max_length=50)
    unlocked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "color_code")

    def __str__(self):
        return f"{self.color_code}"


class Avatar(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name="avatar")
    avatar_type = models.CharField(max_length=20, choices=AvatarType.choices, default=AvatarType.BOY)
    hair_item = models.ForeignKey(UserUnlockedItem, on_delete=models.PROTECT, related_name="selected_as_hair")
    hair_color = models.ForeignKey(UserUnlockedColor, on_delete=models.PROTECT, related_name="used_for_hair")
    face_item = models.ForeignKey(UserUnlockedItem, on_delete=models.PROTECT, related_name="selected_as_face")
    eyes_color = models.ForeignKey(UserUnlockedEyesColor, on_delete=models.PROTECT, related_name="used_for_eyes")
    shirt_item = models.ForeignKey(UserUnlockedItem, on_delete=models.PROTECT, related_name="selected_as_shirt")
    shirt_color = models.ForeignKey(UserUnlockedColor, on_delete=models.PROTECT, related_name="used_for_shirt")
    pants_item = models.ForeignKey(UserUnlockedItem, on_delete=models.PROTECT, related_name="selected_as_pants")
    pants_color = models.ForeignKey(UserUnlockedColor, on_delete=models.PROTECT, related_name="used_for_pants")
    shoes_item = models.ForeignKey(UserUnlockedItem, on_delete=models.PROTECT, related_name="selected_as_shoes")
    shoes_color = models.ForeignKey(UserUnlockedColor, on_delete=models.PROTECT, related_name="used_for_shoes")
    accessory_item = models.ForeignKey(
        UserUnlockedItem, null=True, blank=True, on_delete=models.SET_NULL, related_name="selected_as_accessory"
    )
    accessory_color = models.ForeignKey(
        UserUnlockedColor, null=True, blank=True, on_delete=models.SET_NULL, related_name="used_for_accessory"
    )
    skin_color = models.ForeignKey(UserUnlockedSkinColor, on_delete=models.PROTECT, related_name="used_for_skin")
    updated_at = models.DateTimeField(auto_now=True)
