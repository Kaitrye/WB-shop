from decimal import Decimal

from rest_framework import serializers

from balance.models import Balance, BalanceTransaction


class BalanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Balance
        fields = (
            "id",
            "amount",
        )
        read_only_fields = (
            "id",
            "amount",
        )


class BalanceTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = BalanceTransaction
        fields = (
            "id",
            "operation_type",
            "amount",
            "order",
            "performed_at",
        )
        read_only_fields = (
            "id",
            "operation_type",
            "amount",
            "order",
            "performed_at",
        )


class TopUpBalanceSerializer(serializers.Serializer):
    amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal("0.01"),
    )
