"""URL配置"""
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/accounts/", include("accounts.urls")),
    path("api/rooms/", include("rooms.urls")),
    path("api/feedback/", include("feedback.urls")),
    path("api/ai-chat/", include("AiChat.urls")),
    path("api/admin-panel/", include("admin_panel.urls")),
]

# 开发环境暴露媒体文件
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
