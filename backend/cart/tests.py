from decimal import Decimal
from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase

from cart.models import Cart, CartItem
from products.models import Product


User = get_user_model()


class CartEndpointsTests(APITestCase):
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
            name="Available product",
            price=Decimal("199.99"),
            stock=10,
        )
        self.inactive_product = Product.objects.create(
            name="Inactive product",
            price=Decimal("99.99"),
            stock=5,
            is_active=False,
        )
        self.client.force_authenticate(user=self.user)

    def test_get_cart_returns_empty_cart_for_new_user(self):
        response = self.client.get(reverse("cart"))

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.json()["items"], [])
        self.assertTrue(Cart.objects.filter(user=self.user).exists())

    def test_add_item_creates_cart_item(self):
        response = self.client.post(
            reverse("cart-item-create"),
            {"product_id": self.product.id, "quantity": 2},
            format="json",
        )

        self.assertEqual(response.status_code, HTTPStatus.CREATED)
        self.assertEqual(response.json()["quantity"], 2)
        self.assertTrue(
            CartItem.objects.filter(
                cart__user=self.user,
                product=self.product,
                quantity=2,
            ).exists()
        )

    def test_add_existing_item_increases_quantity(self):
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, product=self.product, quantity=2)

        response = self.client.post(
            reverse("cart-item-create"),
            {"product_id": self.product.id, "quantity": 3},
            format="json",
        )

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.json()["quantity"], 5)
        self.assertEqual(CartItem.objects.filter(cart=cart).count(), 1)

    def test_add_item_rejects_inactive_product(self):
        response = self.client.post(
            reverse("cart-item-create"),
            {"product_id": self.inactive_product.id, "quantity": 1},
            format="json",
        )

        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)
        self.assertFalse(CartItem.objects.filter(product=self.inactive_product).exists())

    def test_add_item_rejects_quantity_above_stock(self):
        response = self.client.post(
            reverse("cart-item-create"),
            {"product_id": self.product.id, "quantity": 11},
            format="json",
        )

        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)
        self.assertFalse(CartItem.objects.filter(product=self.product).exists())

    def test_add_existing_item_rejects_quantity_above_stock(self):
        cart = Cart.objects.create(user=self.user)
        item = CartItem.objects.create(cart=cart, product=self.product, quantity=8)

        response = self.client.post(
            reverse("cart-item-create"),
            {"product_id": self.product.id, "quantity": 3},
            format="json",
        )

        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)
        item.refresh_from_db()
        self.assertEqual(item.quantity, 8)

    def test_update_own_cart_item(self):
        cart = Cart.objects.create(user=self.user)
        item = CartItem.objects.create(cart=cart, product=self.product, quantity=2)

        response = self.client.patch(
            reverse("cart-item-detail", kwargs={"pk": item.pk}),
            {"quantity": 5},
            format="json",
        )

        self.assertEqual(response.status_code, HTTPStatus.OK)
        item.refresh_from_db()
        self.assertEqual(item.quantity, 5)

    def test_update_rejects_quantity_above_stock(self):
        cart = Cart.objects.create(user=self.user)
        item = CartItem.objects.create(cart=cart, product=self.product, quantity=2)

        response = self.client.patch(
            reverse("cart-item-detail", kwargs={"pk": item.pk}),
            {"quantity": 11},
            format="json",
        )

        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)
        item.refresh_from_db()
        self.assertEqual(item.quantity, 2)

    def test_delete_own_cart_item(self):
        cart = Cart.objects.create(user=self.user)
        item = CartItem.objects.create(cart=cart, product=self.product, quantity=2)

        response = self.client.delete(
            reverse("cart-item-detail", kwargs={"pk": item.pk})
        )

        self.assertEqual(response.status_code, HTTPStatus.NO_CONTENT)
        self.assertFalse(CartItem.objects.filter(pk=item.pk).exists())

    def test_user_cannot_change_or_delete_other_users_cart_item(self):
        other_cart = Cart.objects.create(user=self.other_user)
        item = CartItem.objects.create(
            cart=other_cart,
            product=self.product,
            quantity=2,
        )
        url = reverse("cart-item-detail", kwargs={"pk": item.pk})

        patch_response = self.client.patch(url, {"quantity": 3}, format="json")
        delete_response = self.client.delete(url)

        self.assertEqual(patch_response.status_code, HTTPStatus.NOT_FOUND)
        self.assertEqual(delete_response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTrue(CartItem.objects.filter(pk=item.pk).exists())

    def test_anonymous_user_cannot_access_cart(self):
        self.client.force_authenticate(user=None)

        response = self.client.get(reverse("cart"))

        self.assertEqual(response.status_code, HTTPStatus.UNAUTHORIZED)
