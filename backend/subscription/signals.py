"""Signal que crea una suscripción Free automáticamente al registrar un usuario."""

import logging

from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

logger = logging.getLogger(__name__)

User = get_user_model()


@receiver(post_save, sender=User)
def create_free_subscription(sender, instance: User, created: bool, **kwargs):
    """Crea una suscripción Free al registrar un nuevo usuario."""
    if not created:
        return

    from .models import Plan, Subscription

    try:
        free_plan = Plan.objects.get(plan_type=Plan.PlanType.FREE)
        Subscription.objects.create(user=instance, plan=free_plan)
        logger.info("Suscripción Free creada para usuario %s", instance.email)
    except Plan.DoesNotExist:
        logger.warning(
            "No se encontró el plan Free. Ejecuta el comando seed_plans."
        )
