"""功能说明：客房业务的 Django Admin 配置。"""
from django.contrib import admin

from .models import Booking, Favorite, Review, Room, RoomType


@admin.register(RoomType)
class RoomTypeAdmin(admin.ModelAdmin):
    """功能说明：房型管理。"""
    list_display = ["id", "name", "price", "capacity", "total_stock", "remaining_stock"]
    list_filter = ["window", "breakfast"]
    search_fields = ["name", "bed_type"]


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    """功能说明：房间管理。"""
    list_display = ["id", "room_number", "room_type", "floor", "status"]
    list_filter = ["status", "floor"]
    search_fields = ["room_number"]


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    """功能说明：订单管理。"""
    list_display = ["id", "user", "room_type", "room", "start_date", "end_date", "status"]
    list_filter = ["status"]
    search_fields = ["user__username", "contact_name"]


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    """功能说明：评价管理。"""
    list_display = ["id", "user", "room_type", "rating", "created_at"]
    list_filter = ["rating"]
    search_fields = ["user__username", "content"]


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """功能说明：收藏管理。"""
    list_display = ["id", "user", "room_type", "created_at"]
    search_fields = ["user__username", "room_type__name"]
