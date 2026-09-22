"""功能说明：AI 对话模块的路由配置。"""
from django.urls import path

from .views import (
    AiChatAPIView,
    AiChatSessionDetailAPIView,
    AiChatSessionListAPIView,
    AiChatStreamAPIView,
)

app_name = "AiChat"

urlpatterns = [
    path("chat/", AiChatAPIView.as_view(), name="chat"),
    path("chat/stream/", AiChatStreamAPIView.as_view(), name="chat-stream"),
    path("sessions/", AiChatSessionListAPIView.as_view(), name="session-list"),
    path("sessions/<str:session_id>/", AiChatSessionDetailAPIView.as_view(),
         name="session-detail"),
]
