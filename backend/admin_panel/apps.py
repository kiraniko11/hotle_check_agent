"""功能说明：管理后台应用配置。"""
from django.apps import AppConfig


class AdminPanelConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "admin_panel"
    verbose_name = "管理后台"
