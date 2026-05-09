"""
Funciones de extracción de contenido por tipo de archivo.
Cada función recibe el path del archivo y retorna texto en formato Markdown.
"""

import fitz  # PyMuPDF
import pytesseract
from docx import Document as DocxDocument
from PIL import Image

from .models import Document


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


# Mapa de FileType → función procesadora
PROCESSORS: dict[str, callable] = {
    Document.FileType.PDF: process_pdf,
    Document.FileType.IMAGE: process_image,
    Document.FileType.DOCX: process_docx,
    Document.FileType.TEXT: process_text,
}
