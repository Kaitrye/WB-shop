from rest_framework.exceptions import NotFound, ValidationError

from django.db import transaction

from balance.models import Balance, BalanceTransaction
from orders.models import Order

from decimal import Decimal


@transaction.atomic
def top_up_balance(*, user, amount):
    balance, _ = Balance.objects.get_or_create(user=user)
    balance = Balance.objects.select_for_update().get(pk=balance.pk)
    
    balance.amount += amount

    balance.save(update_fields=["amount"])

    BalanceTransaction.objects.create(
        balance=balance,
        operation_type=BalanceTransaction.OperationType.TOP_UP,
        amount=amount,
    )

    return balance


@transaction.atomic
def pay_for_order(*, user, order_id):
    order = (
        Order.objects.select_for_update()
        .prefetch_related("items")
        .filter(pk=order_id, user=user)
        .first()
    )

    if order is None:
        raise NotFound("Заказ не найден.")

    if order.status != Order.Status.CREATED:
        raise ValidationError({"order": "Этот заказ уже оплачен."})

    total_amount = sum(
        (
            item.unit_price * item.quantity
            for item in order.items.all()
        ),
        Decimal("0.00"),
    )

    balance, _ = Balance.objects.get_or_create(user=user)
    balance = Balance.objects.select_for_update().get(pk=balance.pk)

    if balance.amount < total_amount:
        raise ValidationError(
            {"balance": "Недостаточно средств на балансе."}
        )

    balance.amount -= total_amount
    balance.save(update_fields=["amount"])

    BalanceTransaction.objects.create(
        balance=balance,
        order=order,
        operation_type=BalanceTransaction.OperationType.PAYMENT,
        amount=total_amount,
    )

    order.status = Order.Status.PAID
    order.save(update_fields=["status", "updated_at"])

    return order