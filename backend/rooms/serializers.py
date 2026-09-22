"""功能说明：客房业务相关的序列化器。"""

from rest_framework import serializers

from .models import Booking, Favorite, Review, Room, RoomType


def build_absolute_media_url(image_path, request) -> str:
    """功能说明：将媒体文件路径拼接为可访问的绝对 URL。"""
    if not image_path:
        return ""
    # 已经是 http/https 绝对地址（兼容旧数据），原样返回。
    if isinstance(image_path, str) and image_path.startswith(("http://", "https://")):
        return image_path
    normalized = str(image_path).lstrip("/")
    if request is not None:
        return request.build_absolute_uri(f"/media/{normalized}")
    return f"/media/{normalized}"


class RoomSerializer(serializers.ModelSerializer):
    """功能说明：序列化物理客房的基础信息。"""

    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Room
        fields = ("id", "room_number", "floor", "status", "status_display")


class RoomTypeSerializer(serializers.ModelSerializer):
    """功能说明：序列化房间类型的基础资料。"""

    rooms = RoomSerializer(many=True, read_only=True)
    cover_image = serializers.SerializerMethodField()

    class Meta:
        model = RoomType
        fields = ("id", "name", "price", "capacity", "area", "bed_type", "window",
                  "breakfast", "description", "cover_image", "total_stock",
                  "remaining_stock", "rooms")

    def get_cover_image(self, obj) -> str:
        """功能说明：把封面图相对路径转换为后端可访问的绝对 URL。"""
        return build_absolute_media_url(obj.cover_image, self.context.get("request"))


class BookingSerializer(serializers.ModelSerializer):
    """功能说明：序列化预订订单实体数据。"""

    username = serializers.CharField(source="user.username", read_only=True)
    room_type_name = serializers.CharField(source="room_type.name", read_only=True)
    room_number = serializers.CharField(source="room.room_number", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Booking
        fields = ("id", "username", "room_type", "room_type_name", "room", "room_number",
                  "start_date", "end_date", "total_price", "status", "status_display",
                  "contact_name", "contact_phone", "id_card", "payment_method", "created_at")


class ReviewSerializer(serializers.ModelSerializer):
    """功能说明：序列化房型评价，并附带评价人展示信息。"""

    username = serializers.CharField(source="user.username", read_only=True)
    avatar = serializers.SerializerMethodField()
    room_type_name = serializers.CharField(source="room_type.name", read_only=True)

    class Meta:
        model = Review
        fields = ("id", "user", "username", "avatar", "room_type", "room_type_name",
                  "rating", "content", "created_at")

    def get_avatar(self, obj) -> str:
        """功能说明：把评价人头像转换为可访问的绝对 URL。"""
        if not obj.user.avatar:
            return ""
        return build_absolute_media_url(obj.user.avatar.name, self.context.get("request"))


class FavoriteSerializer(serializers.ModelSerializer):
    """功能说明：序列化用户的收藏记录，内嵌房型的基本参数以供展示。"""

    room_type_detail = serializers.SerializerMethodField()

    class Meta:
        model = Favorite
        fields = ("id", "room_type", "room_type_detail", "created_at")
        read_only_fields = ("id", "room_type_detail", "created_at")

    def get_room_type_detail(self, obj) -> dict:
        """功能说明：返回收藏房型的完整详情并拼接图片绝对地址。"""
        # 显式把当前序列化上下文传入房型序列化器，避免图片地址退化为相对路径。
        serializer = RoomTypeSerializer(obj.room_type, context=self.context)
        return serializer.data
