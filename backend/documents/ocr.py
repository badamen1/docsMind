"""
OCR Strategy — mirrors the Factory+Strategy pattern of ai_service/.
Free users  → TesseractOCRService
Pro users   → LandingAIOCRService (landingai-ade; reads VISION_AGENT_API_KEY from env)
"""

from abc import ABC, abstractmethod


class OCRService(ABC):
    """Interface for OCR services. Allows swapping Tesseract / Landing AI."""

    @abstractmethod
    def extract_text(self, file_path: str) -> str:
        """Extract text from an image file given its path on disk."""
        ...


class TesseractOCRService(OCRService):
    """OCR with Tesseract — available to all users."""

    def extract_text(self, file_path: str) -> str:
        import pytesseract
        from PIL import Image
        img = Image.open(file_path)
        return pytesseract.image_to_string(img, lang="spa+eng").strip()


class LandingAIOCRService(OCRService):
    """OCR with Landing AI ADE — available to Pro users only."""

    def extract_text(self, file_path: str) -> str:
        from pathlib import Path
        from landingai import parse
        result = parse(Path(file_path))
        return "\n\n".join(
            chunk.text
            for chunk in result.chunks
            if hasattr(chunk, "text") and chunk.text
        ).strip()


def get_ocr_service(user) -> OCRService:
    """Returns the appropriate OCR service based on the user's plan."""
    try:
        plan_type = user.subscription.plan.plan_type
    except Exception:
        plan_type = "free"
    if plan_type == "pro":
        return LandingAIOCRService()
    return TesseractOCRService()
