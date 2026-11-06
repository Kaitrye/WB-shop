from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator

from decimal import Decimal


class Balance(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="balance",
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    def __str__(self):
        return self.user.email


class BalanceTransaction(models.Model):
    class OperationType(models.TextChoices):
        TOP_UP = "top_up", "Пополнение"
        PAYMENT = "payment", "Оплата"

    balance = models.ForeignKey(
        Balance,
        on_delete=models.CASCADE,
        related_name="transactions",
    )
    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.PROTECT,
        related_name="balance_transactions",
        null=True,
        blank=True,
    )
    operation_type = models.CharField(
        max_length=20,
        choices=OperationType.choices,
    )
    amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    performed_at = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return f"{self.operation_type}: {self.amount}"
