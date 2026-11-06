from django.db import transaction
from rest_framework.exceptions import NotFound, ValidationError

from cart.models import CartItem
from orders.models import Order, OrderItem
from products.models import Product


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
            raise ValidationError(
                {"cart_item_ids": "В заказе есть неактивный товар."}
            )

        if item.quantity > product.stock:
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

    CartItem.objects.filter(pk__in=[item.pk for item in cart_items],).delete()

    return order    




