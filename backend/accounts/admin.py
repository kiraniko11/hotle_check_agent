"""Django Admin配置"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    """用户管理"""
    list_display = ["username", "mobile", "role", "is_active", "date_joined"]
    list_filter = ["role", "is_active"]
    search_fields = ["username", "mobile"]
    
    fieldsets = DjangoUserAdmin.fieldsets + (
        ("扩展信息", {"fields": ("mobile", "avatar", "role")}),
    )
