import logging

from django.db import transaction
from rest_framework.exceptions import NotFound, ValidationError

from cart.models import CartItem
from orders.models import Order, OrderItem
from products.models import Product


logger = logging.getLogger("shop")


@transaction.atomic
def create_order_from_cart(*, user, cart_item_ids):
    cart_items = list(
        CartItem.objects.select_for_update()
        .filter(
            cart__user=user,
            id__in=cart_item_ids,
        )
        .order_by("id")
    )

    if len(cart_items) != len(cart_item_ids):
        logger.warning(
            "event=order_create_rejected user_id=%s reason=cart_item_not_found",
            user.pk,
        )
        raise NotFound("Выбранная позиция корзины не найдена.")

    product_ids = [item.product_id for item in cart_items]
    products_by_id = {
        product.id: product
        for product in Product.objects.select_for_update()
        .filter(id__in=product_ids)
        .order_by("id")
    }

    for item in cart_items:
        product = products_by_id[item.product_id]

        if not product.is_active:
            logger.warning(
                "event=order_create_rejected user_id=%s product_id=%s reason=inactive_product",
                user.pk,
                product.pk,
            )
            raise ValidationError(
                {"cart_item_ids": "В заказе есть неактивный товар."}
            )

        if item.quantity > product.stock:
            logger.warning(
                "event=order_create_rejected user_id=%s product_id=%s reason=insufficient_stock",
                user.pk,
                product.pk,
            )
            raise ValidationError(
                {"cart_item_ids": "Недостаточно товара на складе."}
            )

    order = Order.objects.create(user=user)
    for item in cart_items:
        product = products_by_id[item.product_id]

        OrderItem.objects.create(
            order=order,
            product=product,
            product_name=product.name,
            unit_price=product.price,
            quantity=item.quantity,
        )
        product.stock -= item.quantity
        product.save(update_fields=["stock", "updated_at"])

    CartItem.objects.filter(pk__in=[item.pk for item in cart_items]).delete()
    transaction.on_commit(
        lambda: logger.info(
            "event=order_created order_id=%s user_id=%s item_count=%s",
            order.pk,
            user.pk,
            len(cart_items),
        )
    )
    return order
