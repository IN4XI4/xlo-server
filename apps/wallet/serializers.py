from rest_framework import serializers
from .models import CoinPackage, CoinPurchase


class CoinPackageSerializer(serializers.ModelSerializer):
    price_display = serializers.SerializerMethodField()

    class Meta:
        model = CoinPackage
        fields = ["id", "name", "coins", "price_cents", "currency", "price_display"]

    def get_price_display(self, obj):
        return f"{obj.price_cents / 100:.2f} {obj.currency}"


class CoinPurchaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = CoinPurchase
        fields = ["id", "package", "coins", "price_cents", "currency", "status", "created_at"]


class LedgerEntrySerializer(serializers.Serializer):
    id = serializers.IntegerField()
    entry_type = serializers.CharField()
    amount = serializers.IntegerField()
    created_at = serializers.DateTimeField()
    detail = serializers.SerializerMethodField()

    def get_detail(self, obj):
        purchases = self.context.get("purchases", {})
        spends = self.context.get("spends", {})

        ref = obj.reference_id

        if obj.entry_type == "credit":
            if ref.startswith("purchase:"):
                purchase_id = ref.split(":", 1)[1]
                purchase = purchases.get(purchase_id)
                if purchase:
                    return {
                        "type": "purchase",
                        "package_name": purchase.package.name,
                        "coins": purchase.coins,
                        "price_cents": purchase.price_cents,
                        "price_display": f"{purchase.price_cents / 100:.2f} {purchase.currency}",
                        "currency": purchase.currency,
                    }
            return {"type": ref}

        if obj.entry_type == "debit":
            if ref.startswith("spend:"):
                spend_id = int(ref.split(":", 1)[1])
                spend = spends.get(spend_id)
                if spend:
                    return self._get_spend_detail(spend)
            return {"type": ref}

        return {"type": ref}

    def _get_spend_detail(self, spend):
        from apps.wallet.models import CoinSpend

        base = {"type": "spend", "reason": spend.reason, "coins": spend.coins}

        if spend.reason == CoinSpend.Reason.BUY_ITEM:
            item = self.context.get("avatar_items", {}).get(int(spend.target_id))
            if item:
                base["item"] = {
                    "id": item.id,
                    "name": item.name,
                    "code": item.code,
                    "item_type": item.item_type,
                    "avatar_type": item.avatar_type,
                    "svg": item.svg,
                }

        elif spend.reason == CoinSpend.Reason.BUY_COLOR:
            if spend.target_type == "item_color":
                color = self.context.get("item_colors", {}).get(int(spend.target_id))
                if color:
                    base["color"] = {"id": color.id, "name": color.name, "code": color.code, "hex": color.hex}
            elif spend.target_type == "skin_color":
                skin = self.context.get("skin_colors", {}).get(int(spend.target_id))
                if skin:
                    base["color"] = {
                        "id": skin.id,
                        "name": skin.name,
                        "code": skin.code,
                        "main_color": skin.main_color,
                        "second_color": skin.second_color,
                    }

        return base
