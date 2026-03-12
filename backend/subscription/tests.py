from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from users.models import User
from subscription.models import Plan, Subscription


class PlanModelTestCase(TestCase):
    """Tests para el modelo Plan."""

    def setUp(self):
        self.free_plan = Plan.objects.create(
            plan_type=Plan.PlanType.FREE,
            name="Free",
            price="0.00",
            description="Plan gratuito",
            max_documents=5,
            max_storage_mb=10,
        )
        self.pro_plan = Plan.objects.create(
            plan_type=Plan.PlanType.PRO,
            name="Pro",
            price="9.99",
            description="Plan pro",
            max_documents=100,
            max_storage_mb=1024,
        )

    def test_str_representation(self):
        """El string del plan muestra nombre y precio."""
        self.assertIn("Free", str(self.free_plan))
        self.assertIn("0.00", str(self.free_plan))

    def test_ordering_by_price(self):
        """Los planes se ordenan por precio (Free primero)."""
        plans = list(Plan.objects.all())
        self.assertEqual(plans[0].plan_type, Plan.PlanType.FREE)
        self.assertEqual(plans[1].plan_type, Plan.PlanType.PRO)


class SubscriptionModelTestCase(TestCase):
    """Tests para el modelo Subscription y sus métodos."""

    def setUp(self):
        self.free_plan = Plan.objects.create(
            plan_type=Plan.PlanType.FREE,
            name="Free",
            price="0.00",
            description="Plan gratuito",
            max_documents=5,
            max_storage_mb=10,
        )
        self.pro_plan = Plan.objects.create(
            plan_type=Plan.PlanType.PRO,
            name="Pro",
            price="9.99",
            description="Plan pro",
            max_documents=100,
            max_storage_mb=1024,
        )
        self.user = User.objects.create_user(
            email="test@docsmind.com",
            username="testuser",
            password="TestPass123!",
        )

    def test_subscription_created_on_user_register(self):
        """La señal crea una suscripción Free al registrar el usuario."""
        self.assertTrue(hasattr(self.user, "subscription"))
        sub = self.user.subscription
        self.assertEqual(sub.plan, self.free_plan)
        self.assertEqual(sub.status, Subscription.Status.ACTIVE)

    def test_upgrade_changes_plan_and_status(self):
        """upgrade() cambia el plan al Pro y mantiene status ACTIVE."""
        sub = self.user.subscription
        sub.upgrade(self.pro_plan)
        sub.refresh_from_db()
        self.assertEqual(sub.plan, self.pro_plan)
        self.assertEqual(sub.status, Subscription.Status.ACTIVE)
        self.assertIsNone(sub.expires_at)

    def test_cancel_downgrades_to_free(self):
        """cancel() cambia el status a CANCELLED y vuelve al plan Free."""
        sub = self.user.subscription
        # Primero subir a Pro
        sub.upgrade(self.pro_plan)
        sub.refresh_from_db()
        self.assertEqual(sub.plan, self.pro_plan)

        # Ahora cancelar
        sub.cancel()
        sub.refresh_from_db()
        self.assertEqual(sub.status, Subscription.Status.CANCELLED)
        self.assertEqual(sub.plan, self.free_plan)

    def test_str_representation(self):
        """El string de Subscription incluye usuario y plan."""
        sub = self.user.subscription
        self.assertIn(str(self.user), str(sub))


class SubscriptionAPITestCase(TestCase):
    """Tests para el endpoint GET /api/subscription/."""

    def setUp(self):
        self.client = APIClient()
        Plan.objects.create(
            plan_type=Plan.PlanType.FREE,
            name="Free",
            price="0.00",
            description="Plan gratuito",
            max_documents=5,
            max_storage_mb=10,
        )
        self.user = User.objects.create_user(
            email="test@docsmind.com",
            username="testuser",
            password="TestPass123!",
        )
        self.client.force_login(self.user)

    def test_get_subscription_authenticated(self):
        """Un usuario autenticado puede ver su suscripción."""
        response = self.client.get("/api/subscription/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("plan", response.data)
        self.assertIn("status", response.data)
        self.assertIn("is_active", response.data)

    def test_get_subscription_unauthenticated(self):
        """Un usuario no autenticado no puede ver la suscripción."""
        self.client.logout()
        response = self.client.get("/api/subscription/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
