"""功能说明：管理后台的路由配置。"""
from django.urls import path

from .views import (
    AdminBookingAPIView,
    AdminFavoriteAPIView,
    AdminFeedbackAPIView,
    AdminLoginAPIView,
    AdminProfileAPIView,
    AdminReviewAPIView,
    AdminRoomAPIView,
    AdminRoomTypeAPIView,
    AdminStatsAPIView,
    AdminUserAPIView,
)

app_name = "admin_panel"

urlpatterns = [
    # 管理员认证与统计。
    path("login/", AdminLoginAPIView.as_view(), name="login"),
    path("profile/", AdminProfileAPIView.as_view(), name="profile"),
    path("stats/", AdminStatsAPIView.as_view(), name="stats"),

    # 通用资源增删改查：列表与新增。
    path("users/", AdminUserAPIView.as_view(), name="user-list"),
    path("room-types/", AdminRoomTypeAPIView.as_view(), name="room-type-list"),
    path("rooms/", AdminRoomAPIView.as_view(), name="room-list"),
    path("bookings/", AdminBookingAPIView.as_view(), name="booking-list"),
    path("feedbacks/", AdminFeedbackAPIView.as_view(), name="feedback-list"),
    path("reviews/", AdminReviewAPIView.as_view(), name="review-list"),
    path("favorites/", AdminFavoriteAPIView.as_view(), name="favorite-list"),

    # 通用资源增删改查：详情、更新与删除。
    path("users/<int:pk>/", AdminUserAPIView.as_view(), name="user-detail"),
    path("room-types/<int:pk>/", AdminRoomTypeAPIView.as_view(), name="room-type-detail"),
    path("rooms/<int:pk>/", AdminRoomAPIView.as_view(), name="room-detail"),
    path("bookings/<int:pk>/", AdminBookingAPIView.as_view(), name="booking-detail"),
    path("feedbacks/<int:pk>/", AdminFeedbackAPIView.as_view(), name="feedback-detail"),
    path("reviews/<int:pk>/", AdminReviewAPIView.as_view(), name="review-detail"),
    path("favorites/<int:pk>/", AdminFavoriteAPIView.as_view(), name="favorite-detail"),
]
