from django.urls import path

from . import views

urlpatterns = [
    path("upload/", views.upload_document, name="document-upload"),
    path("", views.list_documents, name="document-list"),
    path("<uuid:document_id>/", views.get_document, name="document-detail"),
    path("<uuid:document_id>/delete/", views.delete_document, name="document-delete"),
]
