"""功能说明：AI 对话模块的 Django Admin 配置。"""
from django.contrib import admin

from .models import AiChatMessage, AiChatSession


class AiChatMessageInline(admin.TabularInline):
    """功能说明：在会话详情中内联展示消息记录。"""
    model = AiChatMessage
    extra = 0
    fields = ("role", "kind", "content", "created_at")
    readonly_fields = ("created_at",)


@admin.register(AiChatSession)
class AiChatSessionAdmin(admin.ModelAdmin):
    """功能说明：AI 对话会话管理。"""
    list_display = ("id", "user", "title", "session_id", "updated_at")
    search_fields = ("user__username", "title", "session_id")
    inlines = (AiChatMessageInline,)


@admin.register(AiChatMessage)
class AiChatMessageAdmin(admin.ModelAdmin):
    """功能说明：AI 对话消息管理。"""
    list_display = ("id", "session", "role", "kind", "created_at")
    list_filter = ("role", "kind")
    search_fields = ("content",)
