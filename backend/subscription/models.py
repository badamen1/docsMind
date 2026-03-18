from django.conf import settings
from django.db import models


class Plan(models.Model):
    """
    Planes de suscripción disponibles.
    Se poblan via datos iniciales (fixtures) o migraciones.
    """

    class PlanType(models.TextChoices):
        FREE = "free", "Free"
        PRO = "pro", "Pro"

    # Catálogo de planes con sus atributos por defecto
    PLAN_CATALOG = {
        PlanType.FREE: {
            "name": "Free",
            "price": "0.00",
            "description": "Acceso básico: hasta 5 documentos y 10 MB de almacenamiento.",
            "max_documents": 5,
            "max_storage_mb": 10,
        },
        PlanType.PRO: {
            "name": "Pro",
            "price": "9.99",
            "description": "Acceso avanzado: hasta 100 documentos y 1 GB de almacenamiento.",
            "max_documents": 100,
            "max_storage_mb": 1024,
        },
    }

    plan_type = models.CharField(
        max_length=20,
        choices=PlanType.choices,
        unique=True,
    )
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    max_documents = models.PositiveIntegerField(null=True, blank=True)
    max_storage_mb = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} (${self.price}/mes)"

    class Meta:
        ordering = ["price"]


class Subscription(models.Model):
    """
    Suscripción activa de un usuario. Cada usuario tiene una única suscripción.
    Por defecto se asigna el plan Free.

    Métodos clave:
    - upgrade(plan): sube al plan indicado (futuro: webhook de Stripe).
    - cancel(): cancela y hace downgrade a Free (principio DRY).
    """

    class Status(models.TextChoices):
        ACTIVE = "active", "Activa"
        CANCELLED = "cancelled", "Cancelada"
        EXPIRED = "expired", "Expirada"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="subscription",
    )
    plan = models.ForeignKey(
        Plan,
        on_delete=models.PROTECT,
        related_name="subscriptions",
        null=True,
        blank=True,
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    started_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # ------------------------------------------------------------------
    #  Helpers
    # ------------------------------------------------------------------

    def _get_free_plan(self):
        return Plan.objects.filter(plan_type=Plan.PlanType.FREE).first()

    # ------------------------------------------------------------------
    #  Métodos de negocio
    # ------------------------------------------------------------------

    def save(self, *args, **kwargs):
        """Asigna el plan Free por defecto si no se especifica ningún plan."""
        if self.plan is None:
            self.plan = self._get_free_plan()
        super().save(*args, **kwargs)

    def upgrade(self, plan: "Plan") -> None:
        """
        Sube al usuario al plan indicado y reactiva la suscripción.
        Uso futuro: llamar desde el webhook de Stripe al confirmar el pago.
        """
        self.plan = plan
        self.status = Subscription.Status.ACTIVE
        self.expires_at = None
        self.save(update_fields=["plan", "status", "expires_at", "updated_at"])

    def cancel(self) -> None:
        """
        Cancela la suscripción y hace downgrade al plan Free.
        Usa update() para evitar disparar post_save de nuevo (DRY).
        """
        free_plan = self._get_free_plan()
        Subscription.objects.filter(pk=self.pk).update(
            status=Subscription.Status.CANCELLED,
            plan=free_plan,
        )
        # Sincronizar instancia local
        self.status = Subscription.Status.CANCELLED
        self.plan = free_plan

    def __str__(self):
        return f"{self.user} → {self.plan} [{self.status}]"

    class Meta:
        verbose_name = "Suscripción"
        verbose_name_plural = "Suscripciones"