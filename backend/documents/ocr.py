"""
OCR Strategy — mirrors the Factory+Strategy pattern of ai_service/.
Free users  → TesseractOCRService
Pro users   → LandingAIOCRService (landingai-ade; reads VISION_AGENT_API_KEY from env)
"""

from abc import ABC, abstractmethod

from subscription.models import Plan


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
        import os
        from landingai_ade import LandingAIADE
        client = LandingAIADE(api_key=os.environ["VISION_AGENT_API_KEY"])
        with open(file_path, "rb") as f:
            result = client.parse(document=f)
        return result.markdown or ""


def get_ocr_service(user) -> OCRService:
    """Returns the appropriate OCR service based on the user's plan."""
    plan_type = getattr(
        getattr(getattr(user, "subscription", None), "plan", None),
        "plan_type",
        "free",
    )
    if plan_type == Plan.PlanType.PRO:
        return LandingAIOCRService()
    return TesseractOCRService()
