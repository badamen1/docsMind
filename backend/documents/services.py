"""
Lógica de negocio para el módulo de documentos.
Las vistas solo delegan aquí — ninguna lógica de dominio vive en views.py.
"""

import logging

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Sum

from .models import Document
from .processors import PROCESSORS

logger = logging.getLogger(__name__)


class DocumentService:

    @staticmethod
    def validate_plan_limits(user, file_size: int) -> None:
        """
        Valida que el usuario no supere los límites de documentos y
        almacenamiento definidos en su plan de suscripción.

        Raises:
            ValidationError: Si se supera algún límite del plan o el usuario
                             no tiene suscripción/plan asignado.
        """
        # Guardia: verificar que el usuario tiene suscripción con plan asignado
        subscription = getattr(user, "subscription", None)
        plan = getattr(subscription, "plan", None) if subscription else None

        if plan is None:
            raise ValidationError(
                "Tu cuenta no tiene un plan activo. Contacta al soporte."
            )

        # Validar cantidad de documentos
        doc_count = Document.objects.filter(user=user).count()
        if plan.max_documents is not None and doc_count >= plan.max_documents:
            raise ValidationError(
                f"Has alcanzado el límite de {plan.max_documents} documentos de tu plan."
            )

        # Validar almacenamiento total
        total_bytes = (
            Document.objects.filter(user=user).aggregate(total=Sum("file_size"))["total"] or 0
        )
        max_bytes = (plan.max_storage_mb or 0) * 1024 * 1024
        if total_bytes + file_size > max_bytes:
            raise ValidationError(
                f"Has excedido el límite de almacenamiento de {plan.max_storage_mb} MB de tu plan."
            )

    @staticmethod
    @transaction.atomic
    def create_document(user, file, file_type: str) -> Document:
        """
        Crea el registro del documento en BD y dispara el procesamiento.
        Usa @transaction.atomic para garantizar consistencia: si el
        procesamiento falla, el documento queda en estado FAILED (no se revierte).
        """
        document = Document.objects.create(
            user=user,
            file=file,
            file_name=file.name,
            file_type=file_type,
            file_size=file.size,
        )
        DocumentService._process_document(document)
        return document

    @staticmethod
    def _process_document(document: Document) -> None:
        """
        Pipeline interno de extracción de contenido.
        Actualiza el estado del documento en cada paso.
        """
        document.status = Document.Status.PROCESSING
        document.save(update_fields=["status", "updated_at"])

        try:
            processor_fn = PROCESSORS.get(document.file_type)
            if processor_fn is None:
                raise ValueError(f"No hay procesador para el tipo: {document.file_type}")

            markdown = processor_fn(document.file.path)

            document.markdown_content = markdown.strip()
            document.status = Document.Status.COMPLETED
            document.error_message = ""
            document.save(
                update_fields=["markdown_content", "status", "error_message", "updated_at"]
            )
            logger.info("Documento %s procesado exitosamente.", document.id)

        except Exception as exc:
            document.status = Document.Status.FAILED
            document.error_message = str(exc)
            document.save(update_fields=["status", "error_message", "updated_at"])
            logger.error("Error procesando documento %s: %s", document.id, exc)

    @staticmethod
    @transaction.atomic
    def delete_document(document: Document) -> None:
        """
        Elimina el registro de BD y el archivo físico del disco.
        Usa @transaction.atomic para que si falla el delete de BD,
        el archivo no se borre tampoco.
        """
        document.file.delete(save=False)
        document.delete()
        logger.info("Documento %s eliminado.", document.id)
