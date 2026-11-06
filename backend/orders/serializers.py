from rest_framework import serializers

from orders.models import Order, OrderItem
from products.serializers import ProductSerializer


class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)

    class Meta:
        model = OrderItem
        fields = (
            "id",
            "product",
            "product_name",
            "unit_price",
            "quantity",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id", 
            "product",
            "product_name", 
            "unit_price", 
            "quantity",
            "created_at",
            "updated_at",
        )


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = (
            "id",
            "status",
            "items",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "status",
            "items",
            "created_at",
            "updated_at",
        )


class CreateOrderSerializer(serializers.Serializer):
    cart_item_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        allow_empty=False,
    )

    def validate_cart_item_ids(self, value):
        if len(value) != len(set(value)):
            raise serializers.ValidationError(
                "Одна позиция корзины не может быть выбрана дважды."
            )
        return value
