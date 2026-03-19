from django.urls import path

from .views import ChatDetailView, ChatListView, CreateChatView, SendMessageView

urlpatterns = [
    path("", ChatListView.as_view(), name="chat-list"),
    path("create/", CreateChatView.as_view(), name="chat-create"),
    path("<uuid:id>/", ChatDetailView.as_view(), name="chat-detail"),
    path("<uuid:id>/messages/", SendMessageView.as_view(), name="chat-messages"),
]

