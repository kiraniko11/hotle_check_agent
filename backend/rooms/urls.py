"""功能说明：客房业务的路由配置。"""
from django.urls import path

from .views import (
    BookingCancelView,
    BookingCreateView,
    FavoriteStatusView,
    FavoriteToggleView,
    ReviewEligibilityView,
    ReviewBoardView,
    ReviewListCreateView,
    RoomStatsView,
    RoomTypeDetailView,
    RoomTypeListView,
    UserBookingListView,
    UserFavoriteListView,
)

app_name = "rooms"

urlpatterns = [
    # 房型查询与详情。
    path("types/", RoomTypeListView.as_view(), name="type-list"),
    path("types/<int:pk>/", RoomTypeDetailView.as_view(), name="type-detail"),
    path("stats/", RoomStatsView.as_view(), name="stats"),

    # 收藏相关接口。
    path("types/<int:pk>/favorite/", FavoriteToggleView.as_view(), name="favorite-toggle"),
    path("types/<int:pk>/favorite/status/", FavoriteStatusView.as_view(), name="favorite-status"),
    path("reviews/", ReviewBoardView.as_view(), name="review-board"),
    path("favorites/", UserFavoriteListView.as_view(), name="favorite-list"),

    # 预订与订单接口。
    path("types/<int:pk>/book/", BookingCreateView.as_view(), name="booking-create"),
    path("bookings/", UserBookingListView.as_view(), name="booking-list"),
    path("bookings/<int:pk>/cancel/", BookingCancelView.as_view(), name="booking-cancel"),

    # 评价接口。
    path("types/<int:pk>/reviews/", ReviewListCreateView.as_view(), name="review-list-create"),
    path("types/<int:pk>/review-eligibility/", ReviewEligibilityView.as_view(),
         name="review-eligibility"),
]
