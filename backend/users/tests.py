from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from users.models import User


class AuthTestCase(TestCase):
    """Tests básicos para registro, login y logout."""

    def setUp(self):
        self.client = APIClient()
        self.register_data = {
            "email": "test@docsmind.com",
            "username": "testuser",
            "password": "TestPass123!",
            "password_confirm": "TestPass123!",
        }

    def test_register_success(self):
        """Un usuario se puede registrar con datos válidos."""
        response = self.client.post("/api/register/", self.register_data)
        self.assertIn(response.status_code, [status.HTTP_201_CREATED, status.HTTP_200_OK])
        self.assertTrue(User.objects.filter(email="test@docsmind.com").exists())

    def test_register_duplicate_email(self):
        """No se puede registrar con un email existente."""
        User.objects.create_user(
            email="test@docsmind.com", username="existing", password="pass"
        )
        response = self.client.post("/api/register/", self.register_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_success(self):
        """Un usuario registrado puede hacer login."""
        User.objects.create_user(
            email="test@docsmind.com", username="testuser", password="TestPass123!"
        )
        response = self.client.post(
            "/api/login/", {"email": "test@docsmind.com", "password": "TestPass123!"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_login_wrong_password(self):
        """Login falla con contraseña incorrecta."""
        User.objects.create_user(
            email="test@docsmind.com", username="testuser", password="TestPass123!"
        )
        response = self.client.post(
            "/api/login/", {"email": "test@docsmind.com", "password": "wrong"}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_logout(self):
        """Un usuario logueado puede cerrar sesión."""
        user = User.objects.create_user(
            email="test@docsmind.com", username="testuser", password="TestPass123!"
        )
        self.client.force_login(user)
        response = self.client.post("/api/logout/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_logout_unauthenticated(self):
        """Logout sin autenticar devuelve 403."""
        response = self.client.post("/api/logout/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
