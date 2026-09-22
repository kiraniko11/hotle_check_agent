"""功能说明：留言反馈模块的路由配置。"""
from django.urls import path

from .views import FeedbackListCreateView

app_name = "feedback"

urlpatterns = [
    path("", FeedbackListCreateView.as_view(), name="list-create"),
]
