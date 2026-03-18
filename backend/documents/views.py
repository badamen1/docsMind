import logging

import fitz  # PyMuPDF
import pytesseract
from docx import Document as DocxDocument
from PIL import Image
from rest_framework import status
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response

from .models import Document

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------
#  Funciones de procesamiento por tipo de archivo
# ------------------------------------------------------------------

def process_pdf(file_path: str) -> str:
    """
    Extrae texto de un PDF con PyMuPDF.
    Si el PDF es escaneado (sin texto extraíble), hace OCR por página.
    """
    doc = fitz.open(file_path)
    pages_md: list[str] = []

    for page_num, page in enumerate(doc, start=1):
        text = page.get_text("text").strip()

        if not text:
            # Página sin texto → renderizar a imagen y hacer OCR
            pix = page.get_pixmap(dpi=300)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            text = pytesseract.image_to_string(img, lang="spa+eng").strip()

        if text:
            pages_md.append(f"## Página {page_num}\n\n{text}")

    doc.close()
    return "\n\n---\n\n".join(pages_md)


def process_image(file_path: str) -> str:
    """Extrae texto de una imagen mediante OCR (Tesseract)."""
    img = Image.open(file_path)
    text = pytesseract.image_to_string(img, lang="spa+eng")
    return text.strip()


def process_docx(file_path: str) -> str:
    """Extrae párrafos de un archivo Word (.docx) como Markdown."""
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


def process_text(file_path: str) -> str:
    """Lee un archivo de texto plano directamente."""
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


# Mapa de tipo → función procesadora
PROCESSORS = {
    Document.FileType.PDF: process_pdf,
    Document.FileType.IMAGE: process_image,
    Document.FileType.DOCX: process_docx,
    Document.FileType.TEXT: process_text,
}


def process_document(document: Document) -> None:
    """
    Procesa un Document: detecta tipo, extrae contenido
    y guarda el Markdown resultante.
    """
    document.status = Document.Status.PROCESSING
    document.save(update_fields=["status", "updated_at"])

    try:
        file_path = document.file.path
        processor_fn = PROCESSORS.get(document.file_type)

        if processor_fn is None:
            raise ValueError(f"No hay procesador para el tipo: {document.file_type}")

        markdown = processor_fn(file_path)

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


# ------------------------------------------------------------------
#  Vistas (API endpoints)
# ------------------------------------------------------------------

@api_view(["POST"])
@parser_classes([MultiPartParser])
def upload_document(request):
    """Sube un documento, detecta su tipo y lo procesa a Markdown."""
    file = request.FILES.get("file")
    if not file:
        return Response(
            {"error": "No se envió ningún archivo."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        file_type = Document.detect_file_type(file.name)
    except ValueError as exc:
        return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    document = Document.objects.create(
        user=request.user,
        file=file,
        file_name=file.name,
        file_type=file_type,
        file_size=file.size,
    )

    process_document(document)

    return Response(
        {
            "id": str(document.id),
            "file_name": document.file_name,
            "file_type": document.file_type,
            "status": document.status,
            "markdown_content": document.markdown_content,
            "error_message": document.error_message,
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(["GET"])
def list_documents(request):
    """Lista todos los documentos del usuario autenticado."""
    documents = Document.objects.filter(user=request.user)
    data = [
        {
            "id": str(doc.id),
            "file_name": doc.file_name,
            "file_type": doc.file_type,
            "status": doc.status,
            "file_size": doc.file_size,
            "created_at": doc.created_at.isoformat(),
        }
        for doc in documents
    ]
    return Response(data)


@api_view(["GET"])
def get_document(request, document_id):
    """Obtiene un documento específico con su contenido Markdown."""
    try:
        document = Document.objects.get(id=document_id, user=request.user)
    except Document.DoesNotExist:
        return Response(
            {"error": "Documento no encontrado."},
            status=status.HTTP_404_NOT_FOUND,
        )

    return Response(
        {
            "id": str(document.id),
            "file_name": document.file_name,
            "file_type": document.file_type,
            "status": document.status,
            "file_size": document.file_size,
            "markdown_content": document.markdown_content,
            "error_message": document.error_message,
            "created_at": document.created_at.isoformat(),
        }
    )


@api_view(["DELETE"])
def delete_document(request, document_id):
    """Elimina un documento del usuario."""
    try:
        document = Document.objects.get(id=document_id, user=request.user)
    except Document.DoesNotExist:
        return Response(
            {"error": "Documento no encontrado."},
            status=status.HTTP_404_NOT_FOUND,
        )

    document.file.delete()  # borra el archivo físico
    document.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)
