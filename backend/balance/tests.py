from decimal import Decimal
from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase

from balance.models import Balance, BalanceTransaction
from orders.models import Order, OrderItem
from products.models import Product

User = get_user_model()


class BalanceEndpointsTests(APITestCase):
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
            name="Product",
            price=Decimal("50.00"),
            stock=10,
        )
        self.client.force_authenticate(user=self.user)

    def create_order(self, *, user=None, quantity=2):
        order = Order.objects.create(user=user or self.user)
        OrderItem.objects.create(
            order=order,
            product=self.product,
            product_name=self.product.name,
            unit_price=self.product.price,
            quantity=quantity,
        )
        return order

    def test_get_balance_creates_zero_balance(self):
        response = self.client.get(reverse("balance"))

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.json()["amount"], "0.00")
        self.assertTrue(Balance.objects.filter(user=self.user).exists())

    def test_top_up_increases_balance_and_creates_transaction(self):
        response = self.client.post(
            reverse("balance-top-up"),
            {"amount": "150.00"},
            format="json",
        )

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.json()["amount"], "150.00")

        balance = Balance.objects.get(user=self.user)
        transaction = BalanceTransaction.objects.get(balance=balance)
        self.assertEqual(
            transaction.operation_type,
            BalanceTransaction.OperationType.TOP_UP,
        )
        self.assertEqual(transaction.amount, Decimal("150.00"))
        self.assertIsNone(transaction.order)

    def test_top_up_rejects_non_positive_amount(self):
        response = self.client.post(
            reverse("balance-top-up"),
            {"amount": "0.00"},
            format="json",
        )

        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)
        self.assertFalse(Balance.objects.filter(user=self.user).exists())

    def test_pay_order_decreases_balance_and_marks_order_paid(self):
        balance = Balance.objects.create(user=self.user, amount=Decimal("150.00"))
        order = self.create_order(quantity=2)

        response = self.client.post(
            reverse("order-pay", kwargs={"pk": order.pk}),
            format="json",
        )

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.json()["status"], Order.Status.PAID)

        balance.refresh_from_db()
        order.refresh_from_db()
        self.assertEqual(balance.amount, Decimal("50.00"))
        self.assertEqual(order.status, Order.Status.PAID)

        transaction = BalanceTransaction.objects.get(
            balance=balance,
            order=order,
        )
        self.assertEqual(
            transaction.operation_type,
            BalanceTransaction.OperationType.PAYMENT,
        )
        self.assertEqual(transaction.amount, Decimal("100.00"))

    def test_pay_order_rejects_insufficient_balance_without_changes(self):
        balance = Balance.objects.create(user=self.user, amount=Decimal("99.00"))
        order = self.create_order(quantity=2)

        response = self.client.post(
            reverse("order-pay", kwargs={"pk": order.pk}),
            format="json",
        )

        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)
        balance.refresh_from_db()
        order.refresh_from_db()
        self.assertEqual(balance.amount, Decimal("99.00"))
        self.assertEqual(order.status, Order.Status.CREATED)
        self.assertFalse(
            BalanceTransaction.objects.filter(
                operation_type=BalanceTransaction.OperationType.PAYMENT
            ).exists()
        )

    def test_pay_order_rejects_repeated_payment(self):
        balance = Balance.objects.create(user=self.user, amount=Decimal("200.00"))
        order = self.create_order(quantity=2)
        url = reverse("order-pay", kwargs={"pk": order.pk})

        first_response = self.client.post(url, format="json")
        second_response = self.client.post(url, format="json")

        self.assertEqual(first_response.status_code, HTTPStatus.OK)
        self.assertEqual(second_response.status_code, HTTPStatus.BAD_REQUEST)
        balance.refresh_from_db()
        self.assertEqual(balance.amount, Decimal("100.00"))
        self.assertEqual(
            BalanceTransaction.objects.filter(
                balance=balance,
                order=order,
                operation_type=BalanceTransaction.OperationType.PAYMENT,
            ).count(),
            1,
        )

    def test_user_cannot_pay_other_users_order(self):
        other_order = self.create_order(user=self.other_user)

        response = self.client.post(
            reverse("order-pay", kwargs={"pk": other_order.pk}),
            format="json",
        )

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        other_order.refresh_from_db()
        self.assertEqual(other_order.status, Order.Status.CREATED)
        self.assertFalse(Balance.objects.filter(user=self.user).exists())

    def test_anonymous_user_cannot_access_balance_or_pay_order(self):
        order = self.create_order()
        self.client.force_authenticate(user=None)

        balance_response = self.client.get(reverse("balance"))
        top_up_response = self.client.post(
            reverse("balance-top-up"),
            {"amount": "10.00"},
            format="json",
        )
        pay_response = self.client.post(
            reverse("order-pay", kwargs={"pk": order.pk}),
            format="json",
        )

        self.assertEqual(balance_response.status_code, HTTPStatus.UNAUTHORIZED)
        self.assertEqual(top_up_response.status_code, HTTPStatus.UNAUTHORIZED)
        self.assertEqual(pay_response.status_code, HTTPStatus.UNAUTHORIZED)
