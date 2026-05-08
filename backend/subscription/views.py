import json
import logging

import stripe
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from decouple import config

from .services import SubscriptionService

logger = logging.getLogger(__name__)

STRIPE_WEBHOOK_SECRET = config("STRIPE_WEBHOOK_SECRET", default=None)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def subscribe_view(request):
    """
    Suscribe al usuario a un plan de pago.

    Body:
        - product_id: ID del producto en Stripe (prod_...)
        - payment_method_id: ID del método de pago (pm_...)
    """
    product_id = request.data.get("product_id")
    payment_method_id = request.data.get("payment_method_id")

    if not product_id:
        return Response(
            {"error": "product_id es requerido"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if not payment_method_id:
        return Response(
            {"error": "payment_method_id es requerido"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        result = SubscriptionService.subscribe_user(
            request.user, product_id, payment_method_id
        )
        return Response(result, status=status.HTTP_201_CREATED)
    except Exception as exc:
        logger.error("Error al suscribir usuario %s: %s", request.user.id, exc)
        return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_setup_intent_view(request):
    """
    Crea un SetupIntent de Stripe y retorna el client_secret.
    El frontend usa este client_secret para inicializar PaymentElement.
    """
    try:
        result = SubscriptionService.create_setup_intent(request.user)
        return Response(result, status=status.HTTP_200_OK)
    except Exception as exc:
        logger.error(
            "Error creando SetupIntent para usuario %s: %s", request.user.id, exc
        )
        return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def subscription_detail_view(request):
    """Obtiene el estado de la suscripción del usuario autenticado."""
    try:
        result = SubscriptionService.get_subscription_detail(request.user)
        return Response(result)
    except Exception as exc:
        logger.error("Error obteniendo suscripción del usuario %s: %s", request.user.id, exc)
        return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def cancel_subscription_view(request):
    """
    Cancela la suscripción del usuario.

    Body:
        - immediate: (opcional, default=False) Si True, cancela de inmediato.
    """
    immediate = request.data.get("immediate", False)

    try:
        result = SubscriptionService.cancel_subscription(request.user, immediate=immediate)
        return Response({"status": "success", "message": "Suscripción cancelada exitosamente", "details": result})
    except ValueError as exc:
        return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as exc:
        logger.error("Error cancelando suscripción del usuario %s: %s", request.user.id, exc)
        return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def update_subscription_view(request):
    """
    Cambia el plan de suscripción del usuario.

    Body:
        - product_id: ID del nuevo producto en Stripe (prod_...)
    """
    new_product_id = request.data.get("product_id")
    if not new_product_id:
        return Response(
            {"error": "product_id es requerido"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        result = SubscriptionService.update_subscription(request.user, new_product_id)
        return Response({"status": "success", **result})
    except ValueError as exc:
        return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as exc:
        logger.error("Error actualizando suscripción del usuario %s: %s", request.user.id, exc)
        return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)


@csrf_exempt
@api_view(["POST"])
@permission_classes([AllowAny])
def stripe_webhook_view(request):
    """
    Webhook que recibe y procesa eventos de Stripe.

    Eventos soportados:
        - checkout.session.completed
        - customer.subscription.updated
        - customer.subscription.deleted
        - invoice.paid
        - invoice.payment_failed
    """
    try:
        if STRIPE_WEBHOOK_SECRET:
            sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")
            try:
                event = stripe.Webhook.construct_event(
                    request.body, sig_header, STRIPE_WEBHOOK_SECRET
                )
            except ValueError:
                return JsonResponse({"error": "Invalid payload"}, status=400)
            except stripe.error.SignatureVerificationError:
                return JsonResponse({"error": "Invalid signature"}, status=400)
        else:
            # Sin verificación de firma (SOLO para desarrollo)
            event = json.loads(request.body)

        event_type = event["type"]
        event_data = event["data"]["object"]

        handlers = {
            "checkout.session.completed": SubscriptionService.handle_checkout_completed,
            "customer.subscription.updated": SubscriptionService.handle_subscription_updated,
            "customer.subscription.deleted": SubscriptionService.handle_subscription_canceled,
            "invoice.paid": SubscriptionService.handle_invoice_paid,
            "invoice.payment_failed": SubscriptionService.handle_invoice_failed,
        }

        handler = handlers.get(event_type)
        if handler:
            handler(event_data)
        else:
            logger.debug("Evento de Stripe no procesado: %s", event_type)

        return JsonResponse({"status": "success"}, status=200)

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception as exc:
        logger.error("Webhook error: %s", exc)
        return JsonResponse({"error": str(exc)}, status=500)
