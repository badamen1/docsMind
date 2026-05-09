# Plan Features — Design Spec

**Goal:** Enforce plan limits and unlock premium capabilities (Gemini Pro model, Landing AI OCR) for Pro subscribers.

**Architecture:** Three independent features, each following existing DocsMind patterns (Factory+Strategy, DIP, services layer). No changes to models or migrations required.

**Tech Stack:** Django 6 + DRF, `landingai-ade` (new), `google-generativeai` (existing), Tesseract (existing).

---

## Feature 1: Upload Limits by Plan

### What it does
Enforces `Plan.max_documents` (count) and `Plan.max_storage_mb` (total bytes) before any file is saved. Free plan: 5 docs / 10 MB. Pro plan: 100 docs / 1 GB.

### Files touched
- **Create:** `backend/documents/services.py`
- **Modify:** `backend/documents/views.py` — `upload_document` view

### Design

`DocumentService` (static class in `documents/services.py`):

```python
class DocumentService:
    @staticmethod
    def check_upload_limits(user, incoming_file_size_bytes: int) -> None:
        """
        Raises PermissionError if the user would exceed their plan limits.
        Must be called before creating the Document record.
        """
        plan = user.subscription.plan
        if plan is None:
            return  # no plan → no limits (shouldn't happen)

        existing_docs = Document.objects.filter(user=user)

        if plan.max_documents is not None:
            count = existing_docs.count()
            if count >= plan.max_documents:
                raise PermissionError(
                    f"Has alcanzado el límite de {plan.max_documents} documentos de tu plan {plan.name}."
                )

        if plan.max_storage_mb is not None:
            used_bytes = existing_docs.aggregate(total=Sum("file_size"))["total"] or 0
            limit_bytes = plan.max_storage_mb * 1024 * 1024
            if used_bytes + incoming_file_size_bytes > limit_bytes:
                raise PermissionError(
                    f"Has alcanzado el límite de almacenamiento de {plan.max_storage_mb} MB de tu plan {plan.name}."
                )
```

`upload_document` view calls `DocumentService.check_upload_limits(request.user, file.size)` after validating the file type, before `Document.objects.create(...)`. A `PermissionError` returns `HTTP 403`.

### Error response
```json
{"error": "Has alcanzado el límite de 5 documentos de tu plan Free."}
```

---

## Feature 2: Gemini Model Selection for Pro

### What it does
Pro users can include `gemini_model` in the chat message request to choose between `gemini-2.5-flash` (default) and `gemini-2.5-pro`. Free users have the field silently ignored — they always get `gemini-2.5-flash`.

### Files touched
- **Modify:** `backend/ai_service/gemini_service.py`
- **Modify:** `backend/ai_service/factory.py`
- **Modify:** `backend/chats/serializers.py`
- **Modify:** `backend/chats/views.py` — `SendMessageView`

### Design

**`GeminiService.__init__(model=None)`**
```python
def __init__(self, model: str | None = None):
    genai.configure(api_key=settings.GEMINI_API_KEY)
    resolved_model = model or getattr(settings, "GEMINI_MODEL", "gemini-2.5-flash")
    self.model = genai.GenerativeModel(resolved_model)
```

**`get_ai_service(provider, model=None)`**
```python
def get_ai_service(provider: str | None = None, model: str | None = None) -> AIService:
    provider = (provider or getattr(settings, "AI_PROVIDER", "gemini")).lower()
    if provider == "openai":
        from .openai_service import OpenAIService
        return OpenAIService()
    from .gemini_service import GeminiService
    return GeminiService(model=model)
```

**`SendMessageSerializer`** — adds optional `gemini_model` field:
```python
gemini_model = serializers.ChoiceField(
    choices=["gemini-2.5-flash", "gemini-2.5-pro"],
    required=False,
    allow_null=True,
    default=None,
)
```

**`SendMessageView.post`** — gate logic:
```python
requested_model = serializer.validated_data.get("gemini_model")
plan_type = getattr(getattr(request.user, "subscription", None), "plan", None)
is_pro = plan_type and plan_type.plan_type == "pro"

if requested_model and not is_pro:
    return Response(
        {"detail": "La selección de modelo solo está disponible en el Plan Pro."},
        status=status.HTTP_403_FORBIDDEN,
    )

model_to_use = requested_model if is_pro else None
ai_service = get_ai_service(provider, model=model_to_use)
```

---

## Feature 3: Landing AI OCR for Pro

### What it does
Pro users get Landing AI's `aila` (via `landingai-ade`) for OCR on images and scanned PDF pages. Free users continue using Tesseract. The rest of the document processing pipeline is unchanged.

### Files touched
- **Create:** `backend/documents/ocr.py`
- **Create/Modify:** `backend/documents/services.py` (add `DocumentService.process_document`)
- **Modify:** `backend/documents/views.py` — wire OCR service, keep existing functions for now or delegate to services
- **Modify:** `backend/requirements.txt` — add `landingai-ade`
- **Modify:** `backend/.env` — rename `LANDING_AI_API_KEY` → `VISION_AGENT_API_KEY` (SDK reads this env var)

### Design

**`documents/ocr.py`** — Strategy pattern mirroring `ai_service/`:

```python
from abc import ABC, abstractmethod

class OCRService(ABC):
    @abstractmethod
    def extract_text(self, file_path: str) -> str: ...

class TesseractOCRService(OCRService):
    def extract_text(self, file_path: str) -> str:
        from PIL import Image
        import pytesseract
        img = Image.open(file_path)
        return pytesseract.image_to_string(img, lang="spa+eng").strip()

class LandingAIOCRService(OCRService):
    def extract_text(self, file_path: str) -> str:
        from pathlib import Path
        from landingai import parse
        result = parse(Path(file_path))
        return "\n\n".join(
            chunk.text for chunk in result.chunks if hasattr(chunk, "text") and chunk.text
        ).strip()

def get_ocr_service(user) -> OCRService:
    """Returns LandingAI for Pro users, Tesseract for Free."""
    try:
        plan_type = user.subscription.plan.plan_type
    except AttributeError:
        plan_type = "free"
    if plan_type == "pro":
        return LandingAIOCRService()
    return TesseractOCRService()
```

**`documents/services.py`** — adds OCR-aware processing:

`DocumentService.process_document(document, ocr_service: OCRService)` mirrors the existing `process_document` function in `views.py` but:
- `process_image(file_path, ocr_service)` uses `ocr_service.extract_text(file_path)` instead of calling Tesseract directly
- `process_pdf(file_path, ocr_service)` uses `ocr_service.extract_text` for scanned pages (no text layers)
- `process_docx` and `process_text` are unaffected (no OCR needed)

**`upload_document` view** — wires both checks:
```python
DocumentService.check_upload_limits(request.user, file.size)   # Feature 1
ocr_service = get_ocr_service(request.user)                     # Feature 3
DocumentService.process_document(document, ocr_service)
```

### Environment
`.env` change: rename `LANDING_AI_API_KEY` → `VISION_AGENT_API_KEY` (the `landingai-ade` SDK reads this env var automatically).

---

## Testing Plan

- **Feature 1:** Upload 6th document as Free user → 403. Upload with file that exceeds storage → 403. Pro user can upload up to 100.
- **Feature 2:** Free user sends `gemini_model: "gemini-2.5-pro"` → 403. Pro user sends it → 200 with Pro model response. Free user omits field → 200 with flash.
- **Feature 3:** Free user uploads image → Tesseract used. Pro user uploads image → Landing AI used. Both paths produce `markdown_content` in the Document.
