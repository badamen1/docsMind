import uuid

from django.conf import settings
from django.db import models


def document_upload_path(instance, filename):
    """Organiza archivos por usuario: documents/<user_id>/<filename>"""
    return f"documents/{instance.user_id}/{filename}"


class Document(models.Model):
    """
    Documento subido por un usuario.
    Al guardarse, se procesa el archivo y se convierte a Markdown.
    """

    class FileType(models.TextChoices):
        PDF = "pdf", "PDF"
        IMAGE = "image", "Imagen"
        DOCX = "docx", "Word (.docx)"
        TEXT = "text", "Texto plano"

        @classmethod
        def from_extension(cls, filename: str) -> str:
            """Detecta el FileType a partir del nombre del archivo."""
            import os
            ext = os.path.splitext(filename)[1].lower()
            file_type = Document.EXTENSION_MAP.get(ext)
            if file_type is None:
                raise ValueError(f"Tipo de archivo no soportado: {ext}")
            return file_type

    class Status(models.TextChoices):
        PENDING = "pending", "Pendiente"
        PROCESSING = "processing", "Procesando"
        COMPLETED = "completed", "Completado"
        FAILED = "failed", "Fallido"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="documents",
    )
    file = models.FileField(upload_to=document_upload_path)
    file_name = models.CharField(max_length=255)
    file_type = models.CharField(
        max_length=10,
        choices=FileType.choices,
    )
    file_size = models.PositiveBigIntegerField(help_text="Tamaño en bytes")
    markdown_content = models.TextField(blank=True, default="")
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    error_message = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # ------------------------------------------------------------------
    # Extensiones soportadas por tipo
    # ------------------------------------------------------------------
    EXTENSION_MAP = {
        ".pdf": FileType.PDF,
        ".png": FileType.IMAGE,
        ".jpg": FileType.IMAGE,
        ".jpeg": FileType.IMAGE,
        ".webp": FileType.IMAGE,
        ".tiff": FileType.IMAGE,
        ".tif": FileType.IMAGE,
        ".docx": FileType.DOCX,
        ".txt": FileType.TEXT,
        ".md": FileType.TEXT,
    }

    @classmethod
    def detect_file_type(cls, filename: str) -> str:
        """Detecta el tipo de archivo a partir de su extensión."""
        import os

        ext = os.path.splitext(filename)[1].lower()
        file_type = cls.EXTENSION_MAP.get(ext)
        if file_type is None:
            raise ValueError(f"Tipo de archivo no soportado: {ext}")
        return file_type

    def __str__(self):
        return f"{self.file_name} ({self.get_status_display()})"

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Documento"
        verbose_name_plural = "Documentos"
