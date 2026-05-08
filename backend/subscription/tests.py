from unittest.mock import MagicMock, patch

from django.test import TestCase
from rest_framework.test import APIClient

from subscription.models import Plan, Subscription
from users.models import User


def _make_user(email="test@example.com"):
    user = User.objects.create_user(
        email=email,
        username=email.split("@")[0],
        password="testpass123",
    )
    return user


class SetupIntentViewTest(TestCase):
    def setUp(self):
        Plan.objects.get_or_create(
            plan_type=Plan.PlanType.FREE,
            defaults={
                "name": "Free",
                "price": "0.00",
                "description": "Free plan",
                "max_documents": 5,
                "max_storage_mb": 10,
            },
        )
        Plan.objects.get_or_create(
            plan_type=Plan.PlanType.PRO,
            defaults={
                "name": "Pro",
                "price": "9.99",
                "description": "Pro plan",
                "max_documents": 100,
                "max_storage_mb": 1024,
            },
        )
        self.user = _make_user()
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    @patch("subscription.stripe_payments_gateway.stripe")
    def test_setup_intent_returns_client_secret(self, mock_stripe):
        mock_stripe.Customer.create.return_value = MagicMock(id="cus_test123")
        mock_stripe.SetupIntent.create.return_value = MagicMock(
            client_secret="seti_test_secret"
        )

        response = self.client.post("/api/subscription/setup-intent/")

        self.assertEqual(response.status_code, 200)
        self.assertIn("client_secret", response.data)
        self.assertEqual(response.data["client_secret"], "seti_test_secret")

    def test_setup_intent_requires_authentication(self):
        unauthenticated = APIClient()
        response = unauthenticated.post("/api/subscription/setup-intent/")
        self.assertEqual(response.status_code, 401)

    @patch("subscription.stripe_payments_gateway.stripe")
    def test_setup_intent_persists_stripe_customer_id(self, mock_stripe):
        mock_stripe.Customer.create.return_value = MagicMock(id="cus_new123")
        mock_stripe.SetupIntent.create.return_value = MagicMock(
            client_secret="seti_secret"
        )

        self.client.post("/api/subscription/setup-intent/")

        self.user.subscription.refresh_from_db()
        self.assertEqual(self.user.subscription.stripe_customer_id, "cus_new123")

    @patch("subscription.stripe_payments_gateway.stripe")
    def test_setup_intent_reuses_existing_customer(self, mock_stripe):
        self.user.subscription.stripe_customer_id = "cus_existing"
        self.user.subscription.save(update_fields=["stripe_customer_id", "updated_at"])

        mock_stripe.SetupIntent.create.return_value = MagicMock(
            client_secret="seti_secret"
        )

        self.client.post("/api/subscription/setup-intent/")

        mock_stripe.Customer.create.assert_not_called()


class SubscriptionDetailViewTest(TestCase):
    def setUp(self):
        Plan.objects.get_or_create(
            plan_type=Plan.PlanType.FREE,
            defaults={
                "name": "Free",
                "price": "0.00",
                "description": "Free plan",
                "max_documents": 5,
                "max_storage_mb": 10,
            },
        )
        Plan.objects.get_or_create(
            plan_type=Plan.PlanType.PRO,
            defaults={
                "name": "Pro",
                "price": "9.99",
                "description": "Pro plan",
                "max_documents": 100,
                "max_storage_mb": 1024,
            },
        )
        self.user = _make_user("detail@example.com")
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_detail_includes_plan_type_when_no_stripe_sub(self):
        response = self.client.get("/api/subscription/detail/")

        self.assertEqual(response.status_code, 200)
        self.assertIn("plan_type", response.data)
        self.assertEqual(response.data["plan_type"], "free")
        self.assertEqual(response.data["status"], "inactive")
