"""
Lógica de negocio para el módulo de documentos.
Las vistas solo delegan aquí — ninguna lógica de dominio vive en views.py.
"""

import logging
import os
import tempfile

import fitz  # PyMuPDF
from docx import Document as DocxDocument
from PIL import Image

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Sum

from .models import Document
from .ocr import OCRService

logger = logging.getLogger(__name__)


class DocumentService:

    @staticmethod
    def check_upload_limits(user, incoming_file_size_bytes: int) -> None:
        """
        Raises PermissionError if the user would exceed their plan limits.
        Call BEFORE creating the Document record.
        """
        try:
            plan = user.subscription.plan
        except ObjectDoesNotExist:
            return  # no subscription → no limits

        if plan is None:
            return

        existing = Document.objects.filter(user=user)

        if plan.max_documents is not None:
            count = existing.count()
            if count >= plan.max_documents:
                raise PermissionError(
                    f"Has alcanzado el límite de {plan.max_documents} documentos "
                    f"de tu plan {plan.name}."
                )

        if plan.max_storage_mb is not None:
            used_bytes = existing.aggregate(total=Sum("file_size"))["total"] or 0
            limit_bytes = plan.max_storage_mb * 1024 * 1024
            if used_bytes + incoming_file_size_bytes > limit_bytes:
                raise PermissionError(
                    f"Has alcanzado el límite de almacenamiento de "
                    f"{plan.max_storage_mb} MB de tu plan {plan.name}."
                )

    @staticmethod
    def process_document(document: Document, ocr_service: "OCRService") -> None:
        """
        Processes a Document: extracts content and saves Markdown.
        The ocr_service determines whether Tesseract or Landing AI is used.
        """
        document.status = Document.Status.PROCESSING
        document.save(update_fields=["status", "updated_at"])

        try:
            file_path = document.file.path

            if document.file_type == Document.FileType.PDF:
                markdown = DocumentService._process_pdf(file_path, ocr_service)
            elif document.file_type == Document.FileType.IMAGE:
                markdown = DocumentService._process_image(file_path, ocr_service)
            elif document.file_type == Document.FileType.DOCX:
                markdown = DocumentService._process_docx(file_path)
            elif document.file_type == Document.FileType.TEXT:
                markdown = DocumentService._process_text(file_path)
            else:
                raise ValueError(f"No hay procesador para el tipo: {document.file_type}")

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
    def _process_pdf(file_path: str, ocr_service: "OCRService") -> str:
        pages_md: list[str] = []
        with fitz.open(file_path) as doc:
            for page_num, page in enumerate(doc, start=1):
                text = page.get_text("text").strip()
                if not text:
                    pix = page.get_pixmap(dpi=300)
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    tmp_path = None
                    try:
                        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                            tmp_path = tmp.name
                        img.save(tmp_path)
                        text = ocr_service.extract_text(tmp_path)
                    finally:
                        if tmp_path:
                            os.unlink(tmp_path)
                if text:
                    pages_md.append(f"## Página {page_num}\n\n{text}")
        return "\n\n---\n\n".join(pages_md)

    @staticmethod
    def _process_image(file_path: str, ocr_service: "OCRService") -> str:
        return ocr_service.extract_text(file_path)

    @staticmethod
    def _process_docx(file_path: str) -> str:
        doc = DocxDocument(file_path)
        paragraphs: list[str] = []
        for para in doc.paragraphs:
            text = para.text.strip()
            if not text:
                continue
            style_name = (para.style.name or "").lower()
            if style_name.startswith("heading"):
                try:
                    level = int(style_name.replace("heading", "").strip())
                except ValueError:
                    level = 1
                paragraphs.append(f"{'#' * level} {text}")
            else:
                paragraphs.append(text)
        return "\n\n".join(paragraphs)

    @staticmethod
    def _process_text(file_path: str) -> str:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()

