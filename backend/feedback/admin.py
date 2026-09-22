"""功能说明：留言反馈的 Django Admin 配置。"""
from django.contrib import admin

from .models import Feedback


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    """功能说明：留言反馈管理。"""
    list_display = ["id", "user", "title", "status", "created_at", "replied_at"]
    list_filter = ["status"]
    search_fields = ["user__username", "title", "content"]
