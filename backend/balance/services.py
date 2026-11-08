import logging
from decimal import Decimal

from django.db import transaction
from rest_framework.exceptions import NotFound, ValidationError

from balance.models import Balance, BalanceTransaction
from orders.models import Order

logger = logging.getLogger("shop")


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
    transaction.on_commit(
        lambda: logger.info(
            "event=balance_topped_up user_id=%s amount=%s",
            user.pk,
            amount,
        )
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
        logger.warning(
            "event=order_payment_rejected user_id=%s order_id=%s reason=not_found",
            user.pk,
            order_id,
        )
        raise NotFound("Заказ не найден.")

    if order.status != Order.Status.CREATED:
        logger.warning(
            "event=order_payment_rejected user_id=%s order_id=%s reason=already_paid",
            user.pk,
            order.pk,
        )
        raise ValidationError({"order": "Этот заказ уже оплачен."})

    total_amount = sum(
        (item.unit_price * item.quantity for item in order.items.all()),
        Decimal("0.00"),
    )

    balance, _ = Balance.objects.get_or_create(user=user)
    balance = Balance.objects.select_for_update().get(pk=balance.pk)

    if balance.amount < total_amount:
        logger.warning(
            "event=order_payment_rejected user_id=%s order_id=%s "
            "reason=insufficient_balance",
            user.pk,
            order.pk,
        )
        raise ValidationError({"balance": "Недостаточно средств на балансе."})

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
    transaction.on_commit(
        lambda: logger.info(
            "event=order_paid order_id=%s user_id=%s amount=%s",
            order.pk,
            user.pk,
            total_amount,
        )
    )
    return order
