import os
from decouple import config
import stripe
from django.http import JsonResponse
from users.models import User

# Manejo seguro de excepciones de Stripe
try:
    from stripe.error import StripeError
except ImportError:
    # Fallback para versiones recientes where StripeError no es exportado
    class StripeError(Exception):
        pass

STRIPE_API_KEY = config("STRIPE_API_KEY")
stripe.api_key = STRIPE_API_KEY
FRONTEND_URL = config("FRONTEND_URL", default="http://localhost:3000")


# ============================================================================
# FUNCIONES AUXILIARES DE VALIDACIÓN
# ============================================================================

def validate_user(user):
    """Valida que el usuario sea válido."""
    if not user or not user.email:
        raise ValueError("Usuario inválido o sin email")
    return True


def validate_card_data(card_data):
    """Valida datos de tarjeta."""
    required_fields = ["number", "exp_month", "exp_year", "cvc"]
    if not all(field in card_data for field in required_fields):
        raise ValueError(f"Faltan campos en tarjeta. Requeridos: {required_fields}")
    return True


# ============================================================================
# FUNCIONES DE STRIPE - CUSTOMERS
# ============================================================================

def create_or_get_stripe_customer(user: User, force_new=False) -> str:
    """
    Crea o obtiene un cliente en Stripe.
    
    Args:
        user: Objeto User de Django
        force_new: Si es True, siempre crea uno nuevo
    
    Returns:
        ID del cliente en Stripe (ej: "cus_...")
    
    Raises:
        ValueError: Si el usuario es inválido
        StripeError: Si hay error con Stripe API
    """
    validate_user(user)
    
    try:
        customer = stripe.Customer.create(
            email=user.email,
            name=f"{user.first_name} {user.last_name}".strip(),
            description=f"Usuario DocsMind: {user.id}",
        )
        return customer.id
    except StripeError as e:
        raise Exception(f"Error creando cliente en Stripe: {str(e)}")


# ============================================================================
# FUNCIONES DE STRIPE - PAYMENT METHODS
# ============================================================================

def create_stripe_payment_method(card_data: dict) -> str:
    """
    Crea un método de pago (tarjeta) en Stripe.
    
    Args:
        card_data: Dict con keys: number, exp_month, exp_year, cvc
    
    Returns:
        ID del payment method (ej: "pm_...")
    
    Raises:
        ValueError: Si faltan campos en tarjeta
        StripeError: Si hay error con Stripe API
    """
    validate_card_data(card_data)
    
    try:
        payment_method = stripe.PaymentMethod.create(
            type="card",
            card={
                "number": card_data["number"],
                "exp_month": int(card_data["exp_month"]),
                "exp_year": int(card_data["exp_year"]),
                "cvc": card_data["cvc"],
            },
        )
        return payment_method.id
    except StripeError as e:
        raise Exception(f"Error creando payment method: {str(e)}")


def attach_payment_method_to_customer(payment_method_id: str, customer_id: str) -> None:
    """
    Vincula un payment method a un cliente en Stripe.
    
    Args:
        payment_method_id: ID del payment method (pm_...)
        customer_id: ID del cliente en Stripe (cus_...)
    
    Raises:
        StripeError: Si hay error con Stripe API
    """
    if not payment_method_id or not customer_id:
        raise ValueError("payment_method_id y customer_id son requeridos")
    
    try:
        stripe.PaymentMethod.attach(
            payment_method_id,
            customer=customer_id,
        )
    except StripeError as e:
        raise Exception(f"Error vinculando payment method: {str(e)}")


# ============================================================================
# FUNCIONES DE STRIPE - SUBSCRIPTIONS
# ============================================================================

def get_stripe_product(product_id: str) -> dict:
    """
    Obtiene información de un producto y su precio en Stripe.
    
    Args:
        product_id: ID del producto en Stripe (prod_...)
    
    Returns:
        Dict con keys: id, name, description, price_id, amount, currency
    
    Raises:
        StripeError: Si el producto no existe
    """
    if not product_id:
        raise ValueError("product_id es requerido")
    
    try:
        product = stripe.Product.retrieve(product_id)
        prices = stripe.Price.list(product=product_id, limit=1)
        
        if not prices.data:
            raise ValueError(f"El producto {product_id} no tiene precios asociados")
        
        price = prices.data[0]
        
        return {
            "id": product.id,
            "name": product.name,
            "description": product.description,
            "price_id": price.id,
            "amount": price.unit_amount,
            "currency": price.currency.upper(),
        }
    except ValueError:
        # Re-raise ValueError as is
        raise
    except Exception as e:
        # Captura InvalidRequestError y otros errores de Stripe
        error_msg = str(e)
        if "No such product" in error_msg or "InvalidRequestError" in type(e).__name__:
            raise ValueError(f"Producto no encontrado: {product_id}")
        raise Exception(f"Error obteniendo producto Stripe: {error_msg}")


def create_stripe_subscription(
    customer_id: str, 
    price_id: str, 
    payment_method_id: str = None
) -> str:
    """
    Crea una suscripción en Stripe.
    
    Args:
        customer_id: ID del cliente en Stripe (cus_...)
        price_id: ID del precio en Stripe (price_...)
        payment_method_id: ID del payment method (pm_...), opcional
    
    Returns:
        ID de la suscripción (ej: "sub_...")
    
    Raises:
        ValueError: Si faltan parámetros requeridos
        StripeError: Si hay error creando la suscripción
    """
    if not customer_id or not price_id:
        raise ValueError("customer_id y price_id son requeridos")
    
    try:
        subscription_params = {
            "customer": customer_id,
            "items": [
                {
                    "price": price_id,
                    "quantity": 1,
                }
            ],
            "expand": ["latest_invoice.payment_intent"],
        }
        
        # Si se proporciona payment method, lo configura como default
        if payment_method_id:
            subscription_params["default_payment_method"] = payment_method_id
            subscription_params["payment_behavior"] = "error_if_incomplete"
        
        subscription = stripe.Subscription.create(**subscription_params)
        return subscription.id
    
    except StripeError as e:
        raise Exception(f"Error creando suscripción: {str(e)}")


def create_stripe_setup_intent(customer_id: str) -> str:
    """
    Crea un SetupIntent en Stripe para recopilar un método de pago.

    Args:
        customer_id: ID del cliente en Stripe (cus_...)

    Returns:
        client_secret del SetupIntent (seti_...secret)

    Raises:
        ValueError: Si falta customer_id
        Exception: Si hay error creando el SetupIntent
    """
    if not customer_id:
        raise ValueError("customer_id es requerido")

    try:
        setup_intent = stripe.SetupIntent.create(
            customer=customer_id,
            automatic_payment_methods={"enabled": True},
        )
        return setup_intent.client_secret
    except StripeError as e:
        raise Exception(f"Error creando SetupIntent: {str(e)}")


def cancel_stripe_subscription(subscription_id: str, immediate: bool = False) -> bool:
    """
    Cancela una suscripción en Stripe.
    
    Args:
        subscription_id: ID de la suscripción (sub_...)
        immediate: Si es True, cancela inmediatamente. Si es False, al final del período
    
    Returns:
        bool: True si se canceló exitosamente
    
    Raises:
        ValueError: Si falta subscription_id
        Exception: Si hay error cancelando
    """
    if not subscription_id:
        raise ValueError("subscription_id es requerido")
    
    try:
        params = {
            'at_period_end': not immediate
        }
        stripe.Subscription.delete(subscription_id, **params)
        return True
    except StripeError as e:
        raise Exception(f"Error cancelando suscripción: {str(e)}")


def update_stripe_subscription(subscription_id: str, new_price_id: str) -> str:
    """
    Actualiza el plan de una suscripción en Stripe.
    
    Args:
        subscription_id: ID de la suscripción (sub_...)
        new_price_id: ID del nuevo precio (price_...)
    
    Returns:
        str: ID de la suscripción actualizada
    
    Raises:
        ValueError: Si faltan parámetros
        Exception: Si hay error actualizando
    """
    if not subscription_id or not new_price_id:
        raise ValueError("subscription_id y new_price_id son requeridos")
    
    try:
        # Obtener la suscripción actual para acceder a items
        subscription = stripe.Subscription.retrieve(subscription_id)
        
        # Actualizar el primer item con el nuevo price
        items_update = [{
            'id': subscription.items.data[0].id,
            'price': new_price_id,
        }]
        
        subscription = stripe.Subscription.modify(
            subscription_id,
            items=items_update,
            proration_behavior='create_prorations',
        )
        
        return subscription.id
    except StripeError as e:
        raise Exception(f"Error actualizando suscripción: {str(e)}")

