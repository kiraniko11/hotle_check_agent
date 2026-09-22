"""功能说明：AI 对话应用配置。"""
from django.apps import AppConfig


class AiChatConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "AiChat"
    verbose_name = "AI 智能助手"
