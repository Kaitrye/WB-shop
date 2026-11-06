from decimal import Decimal
from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase

from cart.models import Cart, CartItem
from orders.models import Order, OrderItem
from products.models import Product


User = get_user_model()


class OrderEndpointsTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="user@example.com",
            password="password_12345678910",
        )
        self.other_user = User.objects.create_user(
            email="other@example.com",
            password="password_12345678910",
        )
        self.product = Product.objects.create(
            name="First product",
            price=Decimal("100.00"),
            stock=10,
        )
        self.second_product = Product.objects.create(
            name="Second product",
            price=Decimal("50.00"),
            stock=5,
        )
        self.third_product = Product.objects.create(
            name="Third product",
            price=Decimal("25.00"),
            stock=8,
        )
        self.client.force_authenticate(user=self.user)

    def create_cart_item(self, product, quantity):
        cart, _ = Cart.objects.get_or_create(user=self.user)
        return CartItem.objects.create(
            cart=cart,
            product=product,
            quantity=quantity,
        )

    def test_create_order_from_selected_cart_items(self):
        first_item = self.create_cart_item(self.product, quantity=2)
        second_item = self.create_cart_item(self.second_product, quantity=1)
        remaining_item = self.create_cart_item(self.third_product, quantity=3)

        response = self.client.post(
            reverse("order-list-create"),
            {"cart_item_ids": [first_item.id, second_item.id]},
            format="json",
        )

        self.assertEqual(response.status_code, HTTPStatus.CREATED)
        order = Order.objects.get(pk=response.json()["id"])
        self.assertEqual(order.user, self.user)
        self.assertEqual(order.status, Order.Status.CREATED)

        order_items = OrderItem.objects.filter(order=order).order_by("product_id")
        self.assertEqual(order_items.count(), 2)

        first_order_item = order_items.get(product=self.product)
        self.assertEqual(first_order_item.product_name, "First product")
        self.assertEqual(first_order_item.unit_price, Decimal("100.00"))
        self.assertEqual(first_order_item.quantity, 2)

        self.product.refresh_from_db()
        self.second_product.refresh_from_db()
        self.assertEqual(self.product.stock, 8)
        self.assertEqual(self.second_product.stock, 4)

        self.assertFalse(CartItem.objects.filter(pk=first_item.pk).exists())
        self.assertFalse(CartItem.objects.filter(pk=second_item.pk).exists())
        self.assertTrue(CartItem.objects.filter(pk=remaining_item.pk).exists())

    def test_create_order_rejects_empty_selection(self):
        response = self.client.post(
            reverse("order-list-create"),
            {"cart_item_ids": []},
            format="json",
        )

        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)
        self.assertFalse(Order.objects.filter(user=self.user).exists())

    def test_create_order_rejects_duplicate_cart_item_ids(self):
        item = self.create_cart_item(self.product, quantity=1)

        response = self.client.post(
            reverse("order-list-create"),
            {"cart_item_ids": [item.id, item.id]},
            format="json",
        )

        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)
        self.assertFalse(Order.objects.filter(user=self.user).exists())
        self.assertTrue(CartItem.objects.filter(pk=item.pk).exists())

    def test_create_order_rejects_other_users_cart_item(self):
        other_cart = Cart.objects.create(user=self.other_user)
        other_item = CartItem.objects.create(
            cart=other_cart,
            product=self.product,
            quantity=2,
        )

        response = self.client.post(
            reverse("order-list-create"),
            {"cart_item_ids": [other_item.id]},
            format="json",
        )

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertFalse(Order.objects.filter(user=self.user).exists())
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 10)
        self.assertTrue(CartItem.objects.filter(pk=other_item.pk).exists())

    def test_create_order_rejects_inactive_product_without_changes(self):
        item = self.create_cart_item(self.product, quantity=2)
        self.product.is_active = False
        self.product.save(update_fields=["is_active"])

        response = self.client.post(
            reverse("order-list-create"),
            {"cart_item_ids": [item.id]},
            format="json",
        )

        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)
        self.assertFalse(Order.objects.filter(user=self.user).exists())
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 10)
        self.assertTrue(CartItem.objects.filter(pk=item.pk).exists())

    def test_create_order_rejects_insufficient_stock_without_changes(self):
        item = self.create_cart_item(self.product, quantity=11)

        response = self.client.post(
            reverse("order-list-create"),
            {"cart_item_ids": [item.id]},
            format="json",
        )

        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)
        self.assertFalse(Order.objects.filter(user=self.user).exists())
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 10)
        self.assertTrue(CartItem.objects.filter(pk=item.pk).exists())

    def test_list_returns_only_current_users_orders(self):
        own_order = Order.objects.create(user=self.user)
        other_order = Order.objects.create(user=self.other_user)

        response = self.client.get(reverse("order-list-create"))

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual([order["id"] for order in response.json()], [own_order.id])
        self.assertNotIn(other_order.id, [order["id"] for order in response.json()])

    def test_retrieve_own_order(self):
        order = Order.objects.create(user=self.user)
        OrderItem.objects.create(
            order=order,
            product=self.product,
            product_name=self.product.name,
            unit_price=self.product.price,
            quantity=2,
        )

        response = self.client.get(
            reverse("order-detail", kwargs={"pk": order.pk})
        )

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.json()["id"], order.id)
        self.assertEqual(response.json()["items"][0]["quantity"], 2)

    def test_retrieve_other_users_order_returns_not_found(self):
        other_order = Order.objects.create(user=self.other_user)

        response = self.client.get(
            reverse("order-detail", kwargs={"pk": other_order.pk})
        )

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_anonymous_user_cannot_access_orders(self):
        self.client.force_authenticate(user=None)

        list_response = self.client.get(reverse("order-list-create"))
        create_response = self.client.post(
            reverse("order-list-create"),
            {"cart_item_ids": [1]},
            format="json",
        )

        self.assertEqual(list_response.status_code, HTTPStatus.UNAUTHORIZED)
        self.assertEqual(create_response.status_code, HTTPStatus.UNAUTHORIZED)
