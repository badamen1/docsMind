"""
Lógica de negocio para el módulo de suscripciones.
Las vistas solo delegan aquí — ninguna lógica de dominio vive en views.py.
"""

import logging

import stripe
from django.db import transaction

from .models import Plan, Subscription
from .stripe_payments_gateway import (
    attach_payment_method_to_customer,
    cancel_stripe_subscription,
    create_or_get_stripe_customer,
    create_stripe_setup_intent,
    create_stripe_subscription,
    get_stripe_product,
    update_stripe_subscription,
)

logger = logging.getLogger(__name__)


class SubscriptionService:

    @staticmethod
    @transaction.atomic
    def subscribe_user(user, product_id: str, payment_method_id: str) -> dict:
        """
        Flujo completo para suscribir a un usuario a un plan de pago:
          1. Crea o recupera el customer de Stripe.
          2. Adjunta el método de pago al customer.
          3. Obtiene el precio del producto en Stripe.
          4. Crea la suscripción recurrente en Stripe.
          5. Persiste los IDs de Stripe y actualiza el plan local.

        Returns:
            dict con subscription_id, status y detalles del producto.

        Raises:
            Exception: Cualquier error de Stripe se propaga para que la vista
                       lo capture y retorne el código HTTP adecuado.
        """
        subscription = user.subscription

        # 1. Customer de Stripe
        if subscription.stripe_customer_id:
            customer_id = subscription.stripe_customer_id
        else:
            customer_id = create_or_get_stripe_customer(user)

        # 2. Adjuntar método de pago
        attach_payment_method_to_customer(payment_method_id, customer_id)

        # 3. Precio del producto
        product = get_stripe_product(product_id)

        # 4. Suscripción en Stripe
        stripe_subscription_id = create_stripe_subscription(
            customer_id=customer_id,
            price_id=product["price_id"],
            payment_method_id=payment_method_id,
        )

        # 5. Persistir en BD y subir plan
        subscription.stripe_customer_id = customer_id
        subscription.stripe_subscription_id = stripe_subscription_id
        subscription.stripe_price_id = product["price_id"]
        subscription.save(
            update_fields=[
                "stripe_customer_id",
                "stripe_subscription_id",
                "stripe_price_id",
                "updated_at",
            ]
        )
        pro_plan = Plan.objects.get(plan_type=Plan.PlanType.PRO)
        subscription.upgrade(pro_plan)

        logger.info("Usuario %s suscrito al plan Pro (Stripe: %s).", user.id, stripe_subscription_id)

        return {
            "subscription_id": stripe_subscription_id,
            "status": "success",
            "product": {
                "name": product["name"],
                "amount": product["amount"] / 100,
                "currency": product["currency"],
            },
        }

    @staticmethod
    @transaction.atomic
    def create_setup_intent(user) -> dict:
        """
        Crea un SetupIntent de Stripe para recopilar el método de pago del usuario.
        Si el usuario no tiene customer en Stripe, lo crea y persiste el ID.

        Returns:
            dict con client_secret del SetupIntent.
        """
        subscription = user.subscription

        if subscription.stripe_customer_id:
            customer_id = subscription.stripe_customer_id
        else:
            customer_id = create_or_get_stripe_customer(user)
            subscription.stripe_customer_id = customer_id
            subscription.save(update_fields=["stripe_customer_id", "updated_at"])

        client_secret = create_stripe_setup_intent(customer_id)
        logger.info("SetupIntent creado para usuario %s.", user.id)
        return {"client_secret": client_secret}

    @staticmethod
    @transaction.atomic
    def cancel_subscription(user, immediate: bool = False) -> dict:
        """
        Cancela la suscripción activa del usuario en Stripe y hace downgrade
        al plan Free en la BD local.

        Args:
            immediate: Si True, cancela de inmediato. Si False (default),
                       cancela al final del período actual.

        Raises:
            ValueError: Si el usuario no tiene suscripción activa en Stripe.
        """
        subscription = user.subscription

        if not subscription.stripe_subscription_id:
            raise ValueError("El usuario no tiene suscripción activa en Stripe.")

        result = cancel_stripe_subscription(
            subscription.stripe_subscription_id,
            immediate=immediate,
        )

        # Limpiar IDs de Stripe y hacer downgrade
        subscription.stripe_subscription_id = None
        subscription.stripe_price_id = None
        subscription.save(update_fields=["stripe_subscription_id", "stripe_price_id", "updated_at"])
        subscription.cancel()  # → cambia status a CANCELLED y plan a Free

        logger.info("Suscripción del usuario %s cancelada.", user.id)
        return result

    @staticmethod
    @transaction.atomic
    def update_subscription(user, new_product_id: str) -> dict:
        """
        Cambia el plan de suscripción del usuario en Stripe (con prorrateo).

        Raises:
            ValueError: Si el usuario no tiene suscripción activa.
        """
        subscription = user.subscription

        if not subscription.stripe_subscription_id:
            raise ValueError("El usuario no tiene suscripción activa en Stripe.")

        new_product = get_stripe_product(new_product_id)
        result = update_stripe_subscription(
            subscription.stripe_subscription_id,
            new_product["price_id"],
        )

        subscription.stripe_price_id = new_product["price_id"]
        subscription.save(update_fields=["stripe_price_id", "updated_at"])

        logger.info(
            "Plan del usuario %s actualizado a %s.", user.id, new_product["name"]
        )
        return {"message": f"Plan actualizado a {new_product['name']}", "details": result}

    @staticmethod
    def get_subscription_detail(user) -> dict:
        """
        Retorna el estado de la suscripción.
        Siempre incluye `plan_type` para que el frontend pueda sincronizar el estado.
        """
        subscription = user.subscription
        plan_type = subscription.plan.plan_type if subscription.plan else "free"

        if not subscription.stripe_subscription_id:
            return {
                "status": "inactive",
                "plan_type": plan_type,
                "plan": plan_type,
                "message": "El usuario no tiene suscripción activa en Stripe.",
            }

        stripe_sub = stripe.Subscription.retrieve(subscription.stripe_subscription_id)
        # StripeObject hereda de dict: usar acceso por clave, no por atributo,
        # para evitar que .items() devuelva el método built-in de dict.
        items_list = stripe_sub.get("items", {}).get("data", [])
        item = items_list[0] if items_list else {}
        current_period_start = item.get("current_period_start") or stripe_sub.get("current_period_start")
        current_period_end = item.get("current_period_end") or stripe_sub.get("current_period_end")
        return {
            "status": "success",
            "plan_type": plan_type,
            "subscription": {
                "id": stripe_sub.get("id"),
                "status": stripe_sub.get("status"),
                "current_period_start": current_period_start,
                "current_period_end": current_period_end,
                "cancel_at": stripe_sub.get("cancel_at"),
                "cancel_at_period_end": stripe_sub.get("cancel_at_period_end", False),
                "price_id": subscription.stripe_price_id,
            },
        }

    # ------------------------------------------------------------------
    #  Handlers de webhook de Stripe
    # ------------------------------------------------------------------

    @staticmethod
    def handle_checkout_completed(event_data: dict) -> None:
        """Procesa el evento checkout.session.completed."""
        logger.info("Checkout completado: %s", event_data.get("id"))

    @staticmethod
    def handle_subscription_updated(event_data: dict) -> None:
        """Procesa el evento customer.subscription.updated."""
        logger.info("Suscripción actualizada en Stripe: %s", event_data.get("id"))

    @staticmethod
    def handle_subscription_canceled(event_data: dict) -> None:
        """
        Procesa el evento customer.subscription.deleted.
        Sincroniza el estado CANCELLED en la BD local.
        """
        stripe_subscription_id = event_data.get("id")
        logger.info("Suscripción cancelada en Stripe: %s", stripe_subscription_id)

        try:
            subscription = Subscription.objects.get(
                stripe_subscription_id=stripe_subscription_id
            )
            subscription.cancel()
        except Subscription.DoesNotExist:
            logger.warning(
                "Webhook: suscripción %s no encontrada en BD.", stripe_subscription_id
            )

    @staticmethod
    def handle_invoice_paid(event_data: dict) -> None:
        """
        Procesa invoice.paid: sincroniza el plan Pro en BD como respaldo,
        por si el usuario cerró el navegador antes de que el frontend llamara a /subscribe/.
        """
        stripe_subscription_id = event_data.get("subscription")
        logger.info("Factura pagada para suscripción Stripe: %s", stripe_subscription_id)

        if not stripe_subscription_id:
            return

        try:
            subscription = Subscription.objects.get(
                stripe_subscription_id=stripe_subscription_id
            )
            if subscription.plan.plan_type != Plan.PlanType.PRO:
                pro_plan = Plan.objects.get(plan_type=Plan.PlanType.PRO)
                subscription.upgrade(pro_plan)
                logger.info(
                    "Plan actualizado a Pro via webhook invoice.paid para usuario %s.",
                    subscription.user_id,
                )
        except Subscription.DoesNotExist:
            logger.warning(
                "Webhook invoice.paid: suscripción %s no encontrada en BD.",
                stripe_subscription_id,
            )

    @staticmethod
    def handle_invoice_failed(event_data: dict) -> None:
        """Procesa el evento invoice.payment_failed."""
        logger.warning("Pago fallido para factura: %s", event_data.get("id"))
