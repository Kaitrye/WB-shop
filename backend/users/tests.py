from http import HTTPStatus

from django.test import TestCase
from rest_framework.test import APITestCase

from django.contrib.auth import get_user_model
from django.urls import reverse

class HealthEndpointTests(TestCase):
    def test_health_returns_ok(self):
        response = self.client.get("/health")

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.json(), {"status": "ok"})


User = get_user_model()

class AuthEndpointsTests(APITestCase):
    def setUp(self):
        self.password = "password_12345678910"
        self.user = User.objects.create_user(
            email="alice@example.com", 
            password=self.password
        )
    
    def test_register_creates_user(self):
        email = "mike@example.com"

        response = self.client.post(
            reverse("register"),
            {"email": email, "password": self.password},
            format="json",
        )

        self.assertEqual(response.status_code, HTTPStatus.CREATED)

        created_user = response.json()
        self.assertEqual(created_user["email"], email)
        self.assertTrue(User.objects.filter(email=email).exists())
        self.assertNotIn("password", created_user)

    def test_login_returns_token_pair(self):
        response = self.client.post(
            reverse("login"),
            {"email": self.user.email, "password": self.password},
            format="json", 
        )

        self.assertEqual(response.status_code, HTTPStatus.OK)
        
        token_pair = response.json()

        self.assertIn("refresh", token_pair)
        self.assertIn("access", token_pair)

    def test_refresh_returns_access_token(self):
        refresh = self.client.post(
            reverse("login"),
            {"email": self.user.email, "password": self.password},
            format="json", 
        ).json()["refresh"]

        response = self.client.post(
            reverse("refresh"),
            {"refresh": refresh},
            format="json", 
        )

        self.assertEqual(response.status_code, HTTPStatus.OK)       
        self.assertIn("access", response.json())

    def test_me_returns_current_user(self):
        access = self.client.post(
            reverse("login"),
            {"email": self.user.email, "password": self.password},
            format="json", 
        ).json()["access"]

        response = self.client.get(
            reverse("me"),
            HTTP_AUTHORIZATION = f"Bearer {access}",
            format="json", 
        )

        self.assertEqual(response.status_code, HTTPStatus.OK)       

        me = response.json()

        self.assertEqual(me["id"], self.user.id)
        self.assertEqual(me["email"], self.user.email)

    def test_register_rejects_existing_email(self):
        response = self.client.post(
            reverse("register"),
            {"email": self.user.email, "password": self.password},
            format="json",
        )

        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)

    def test_login_rejects_wrong_password(self):
        response = self.client.post(
            reverse("login"),
            {"email": self.user.email, "password": "wrong-password"},
            format="json",
        )

        self.assertEqual(response.status_code, HTTPStatus.UNAUTHORIZED)

    def test_me_rejects_request_without_access_token(self):
        response = self.client.get(reverse("me"))

        self.assertEqual(response.status_code, HTTPStatus.UNAUTHORIZED)

    def test_refresh_rejects_invalid_token(self):
        response = self.client.post(
            reverse("refresh"),
            {"refresh": "not-a-valid-token"},
            format="json",
        )

        self.assertEqual(response.status_code, HTTPStatus.UNAUTHORIZED)


