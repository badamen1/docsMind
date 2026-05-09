from unittest.mock import patch, MagicMock

from django.core.files.uploadedfile import SimpleUploadedFile
from django.db.models import Sum
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from users.models import User
from documents.models import Document
from subscription.models import Plan
from documents.services import DocumentService
from documents.ocr import get_ocr_service, TesseractOCRService, LandingAIOCRService


class DocumentUploadTestCase(TestCase):
    """Tests básicos para subida y validación de documentos."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="test@docsmind.com", username="testuser", password="pass"
        )
        self.client.force_login(self.user)

    def test_upload_text_file(self):
        """Se puede subir un archivo .txt válido."""
        file = SimpleUploadedFile("test.txt", b"Contenido de prueba", content_type="text/plain")
        response = self.client.post("/api/documents/upload/", {"file": file}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Document.objects.filter(user=self.user).exists())

    def test_upload_invalid_extension(self):
        """Se rechaza un archivo con extensión no soportada."""
        file = SimpleUploadedFile("malicious.exe", b"fake content", content_type="application/octet-stream")
        response = self.client.post("/api/documents/upload/", {"file": file}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_upload_path_traversal_sanitized(self):
        """Django sanitiza nombres con path traversal (quita directorios)."""
        file = SimpleUploadedFile("../../etc/passwd.txt", b"content", content_type="text/plain")
        # Django convierte '../../etc/passwd.txt' → 'passwd.txt' automáticamente
        self.assertNotIn("/", file.name)
        self.assertNotIn("..", file.name)

    def test_upload_unauthenticated(self):
        """Upload sin autenticación devuelve 403."""
        self.client.logout()
        file = SimpleUploadedFile("test.txt", b"Contenido", content_type="text/plain")
        response = self.client.post("/api/documents/upload/", {"file": file}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class DocumentListTestCase(TestCase):
    """Tests básicos para listado de documentos."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="test@docsmind.com", username="testuser", password="pass"
        )
        self.client.force_login(self.user)

    def test_list_documents_empty(self):
        """Un usuario sin documentos recibe una lista vacía."""
        response = self.client.get("/api/documents/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_list_documents_only_own(self):
        """Un usuario solo ve sus propios documentos."""
        other_user = User.objects.create_user(
            email="other@docsmind.com", username="other", password="pass"
        )
        Document.objects.create(
            user=other_user,
            file_name="other.txt",
            file_type=Document.FileType.TEXT,
            file_size=100,
        )
        response = self.client.get("/api/documents/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)


class UploadLimitsTestCase(TestCase):
    """Tests para verificar la aplicación de límites del plan en uploads."""

    def setUp(self):
        self.free_plan, _ = Plan.objects.get_or_create(
            plan_type=Plan.PlanType.FREE,
            defaults={
                "name": "Free", "price": "0.00",
                "description": "Plan gratuito", "max_documents": 5, "max_storage_mb": 10,
            },
        )
        self.pro_plan, _ = Plan.objects.get_or_create(
            plan_type=Plan.PlanType.PRO,
            defaults={
                "name": "Pro", "price": "9.99",
                "description": "Plan pro", "max_documents": 100, "max_storage_mb": 1024,
            },
        )
        self.client = APIClient()
        # Create user AFTER plans so signal finds free_plan and creates subscription
        self.user = User.objects.create_user(
            email="free@test.com", username="freeuser", password="pass"
        )
        self.client.force_authenticate(user=self.user)

    @patch("documents.views.DocumentService.process_document")
    def test_free_user_blocked_at_document_limit(self, mock_process):
        for i in range(5):
            Document.objects.create(
                user=self.user, file_name=f"doc{i}.txt",
                file_type=Document.FileType.TEXT, file_size=100,
            )
        file = SimpleUploadedFile("extra.txt", b"content", content_type="text/plain")
        response = self.client.post("/api/documents/upload/", {"file": file}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("límite", response.data["error"])

    @patch("documents.views.DocumentService.process_document")
    def test_free_user_blocked_at_storage_limit(self, mock_process):
        nine_dot_nine_mb = 9 * 1024 * 1024 + 900 * 1024
        Document.objects.create(
            user=self.user, file_name="large.txt",
            file_type=Document.FileType.TEXT, file_size=nine_dot_nine_mb,
        )
        big_content = b"x" * (200 * 1024)
        file = SimpleUploadedFile("overflow.txt", big_content, content_type="text/plain")
        response = self.client.post("/api/documents/upload/", {"file": file}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("almacenamiento", response.data["error"])

    @patch("documents.views.DocumentService.process_document")
    def test_pro_user_can_upload_beyond_free_limit(self, mock_process):
        self.user.subscription.plan = self.pro_plan
        self.user.subscription.save(update_fields=["plan", "updated_at"])
        for i in range(6):
            Document.objects.create(
                user=self.user, file_name=f"doc{i}.txt",
                file_type=Document.FileType.TEXT, file_size=100,
            )
        file = SimpleUploadedFile("seventh.txt", b"content", content_type="text/plain")
        response = self.client.post("/api/documents/upload/", {"file": file}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_check_upload_limits_raises_on_doc_count(self):
        for i in range(5):
            Document.objects.create(
                user=self.user, file_name=f"doc{i}.txt",
                file_type=Document.FileType.TEXT, file_size=100,
            )
        with self.assertRaises(PermissionError) as ctx:
            DocumentService.check_upload_limits(self.user, 100)
        self.assertIn("5", str(ctx.exception))

    def test_check_upload_limits_raises_on_storage(self):
        Document.objects.create(
            user=self.user, file_name="big.txt",
            file_type=Document.FileType.TEXT, file_size=10 * 1024 * 1024,
        )
        with self.assertRaises(PermissionError) as ctx:
            DocumentService.check_upload_limits(self.user, 1)
        self.assertIn("almacenamiento", str(ctx.exception))


class OCRServiceRoutingTestCase(TestCase):
    """Tests para el factory de OCR según el plan del usuario."""

    def setUp(self):
        self.free_plan, _ = Plan.objects.get_or_create(
            plan_type=Plan.PlanType.FREE,
            defaults={
                "name": "Free", "price": "0.00",
                "description": "Plan gratuito", "max_documents": 5, "max_storage_mb": 10,
            },
        )
        self.pro_plan, _ = Plan.objects.get_or_create(
            plan_type=Plan.PlanType.PRO,
            defaults={
                "name": "Pro", "price": "9.99",
                "description": "Plan pro", "max_documents": 100, "max_storage_mb": 1024,
            },
        )

    def test_free_user_gets_tesseract(self):
        """Usuario Free obtiene TesseractOCRService."""
        user = User.objects.create_user(
            email="free@ocrtest.com", username="freeocrtest", password="TestPass123!"
        )
        service = get_ocr_service(user)
        self.assertIsInstance(service, TesseractOCRService)

    def test_pro_user_gets_landing_ai(self):
        """Usuario Pro obtiene LandingAIOCRService."""
        user = User.objects.create_user(
            email="pro@ocrtest.com", username="proocrtest", password="TestPass123!"
        )
        user.subscription.plan = self.pro_plan
        user.subscription.save(update_fields=["plan", "updated_at"])
        service = get_ocr_service(user)
        self.assertIsInstance(service, LandingAIOCRService)

    def test_user_without_subscription_gets_tesseract(self):
        """Usuario sin suscripción obtiene Tesseract (fallback seguro)."""
        user = User.objects.create_user(
            email="nosub@ocrtest.com", username="nosubocr", password="TestPass123!"
        )
        user.subscription.delete()
        service = get_ocr_service(user)
        self.assertIsInstance(service, TesseractOCRService)


class DocumentServiceProcessTestCase(TestCase):
    """Tests para DocumentService.process_document con OCR inyectado."""

    def setUp(self):
        self.free_plan, _ = Plan.objects.get_or_create(
            plan_type=Plan.PlanType.FREE,
            defaults={
                "name": "Free", "price": "0.00",
                "description": "Plan gratuito", "max_documents": 5, "max_storage_mb": 10,
            },
        )
        self.user = User.objects.create_user(
            email="proc@test.com", username="procuser", password="TestPass123!"
        )

    def test_process_text_document_uses_no_ocr(self):
        """Procesar un .txt no requiere llamar al servicio OCR."""
        import os
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w", encoding="utf-8") as f:
            f.write("Contenido de prueba")
            tmp_path = f.name
        try:
            doc = Document.objects.create(
                user=self.user,
                file_name="test.txt",
                file_type=Document.FileType.TEXT,
                file_size=19,
            )
            # Patch file.path to return the temp file path directly,
            # bypassing Django's FileSystemStorage MEDIA_ROOT boundary check.
            with patch.object(type(doc.file), "path", new_callable=lambda: property(lambda self: tmp_path)):
                mock_ocr = MagicMock(spec=TesseractOCRService)
                DocumentService.process_document(doc, mock_ocr)
            doc.refresh_from_db()
            self.assertEqual(doc.status, Document.Status.COMPLETED)
            self.assertIn("Contenido de prueba", doc.markdown_content)
            mock_ocr.extract_text.assert_not_called()
        finally:
            os.unlink(tmp_path)

    @patch("documents.views.get_ocr_service")
    def test_upload_calls_get_ocr_service(self, mock_get_ocr):
        """upload_document llama a get_ocr_service con el usuario autenticado."""
        mock_ocr = MagicMock(spec=TesseractOCRService)
        mock_ocr.extract_text.return_value = ""
        mock_get_ocr.return_value = mock_ocr
        client = APIClient()
        client.force_authenticate(user=self.user)
        file = SimpleUploadedFile("test.txt", b"hola", content_type="text/plain")
        response = client.post("/api/documents/upload/", {"file": file}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        mock_get_ocr.assert_called_once_with(self.user)
