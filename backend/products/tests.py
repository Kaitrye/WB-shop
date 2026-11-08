from decimal import Decimal
from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase

from products.models import Product

User = get_user_model()


class ProductEndpointsTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="user@example.com",
            password="password_12345678910",
        )
        self.admin = User.objects.create_user(
            email="admin@example.com",
            password="password_12345678910",
            is_staff=True,
        )
        self.product = Product.objects.create(
            name="Active product",
            description="Available for purchase",
            price=Decimal("199.99"),
            stock=10,
        )
        self.inactive_product = Product.objects.create(
            name="Inactive product",
            price=Decimal("99.99"),
            stock=5,
            is_active=False,
        )

    def test_list_returns_only_active_products(self):
        response = self.client.get(reverse("product-list-create"))

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]["id"], self.product.id)

    def test_retrieve_active_product(self):
        response = self.client.get(
            reverse("product-detail", kwargs={"pk": self.product.pk})
        )

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.json()["name"], self.product.name)

    def test_anonymous_user_cannot_create_product(self):
        response = self.client.post(
            reverse("product-list-create"),
            {"name": "New product", "price": "10.00", "stock": 1},
            format="json",
        )

        self.assertEqual(response.status_code, HTTPStatus.UNAUTHORIZED)

    def test_regular_user_cannot_create_product(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            reverse("product-list-create"),
            {"name": "New product", "price": "10.00", "stock": 1},
            format="json",
        )

        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_admin_can_create_product(self):
        self.client.force_authenticate(user=self.admin)

        response = self.client.post(
            reverse("product-list-create"),
            {"name": "New product", "price": "10.00", "stock": 1},
            format="json",
        )

        self.assertEqual(response.status_code, HTTPStatus.CREATED)
        self.assertTrue(Product.objects.filter(name="New product").exists())

    def test_regular_user_cannot_delete_product(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.delete(
            reverse("product-detail", kwargs={"pk": self.product.pk})
        )

        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        self.product.refresh_from_db()
        self.assertTrue(self.product.is_active)

    def test_admin_soft_deletes_product(self):
        self.client.force_authenticate(user=self.admin)

        response = self.client.delete(
            reverse("product-detail", kwargs={"pk": self.product.pk})
        )

        self.assertEqual(response.status_code, HTTPStatus.NO_CONTENT)
        self.product.refresh_from_db()
        self.assertFalse(self.product.is_active)

        response = self.client.get(
            reverse("product-detail", kwargs={"pk": self.product.pk})
        )
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_regular_user_cannot_update_product(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.patch(
            reverse("product-detail", kwargs={"pk": self.product.pk}),
            {"stock": 7},
            format="json",
        )

        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 10)

    def test_admin_can_partially_update_product(self):
        self.client.force_authenticate(user=self.admin)

        response = self.client.patch(
            reverse("product-detail", kwargs={"pk": self.product.pk}),
            {"stock": 7},
            format="json",
        )

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 7)

    def test_admin_can_fully_update_product(self):
        self.client.force_authenticate(user=self.admin)

        response = self.client.put(
            reverse("product-detail", kwargs={"pk": self.product.pk}),
            {
                "name": "Updated product",
                "description": "Updated description",
                "price": "299.99",
                "stock": 3,
                "is_active": True,
            },
            format="json",
        )

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.product.refresh_from_db()
        self.assertEqual(self.product.name, "Updated product")
        self.assertEqual(self.product.description, "Updated description")
        self.assertEqual(self.product.price, Decimal("299.99"))
        self.assertEqual(self.product.stock, 3)
