"""功能说明：管理后台的序列化器集合。"""

import re
from pathlib import Path

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from rest_framework import serializers
from rest_framework_simplejwt.tokens import AccessToken

from accounts.models import User
from feedback.models import Feedback
from rooms.models import Booking, Favorite, Review, Room, RoomType
from rooms.serializers import build_absolute_media_url

# 使用独立的文件存储保存后台后台上传的房型封面图。
MEDIA_STORAGE = FileSystemStorage(location=settings.MEDIA_ROOT)


class AdminLoginSerializer(serializers.Serializer):
    """功能说明：校验管理员登录入参。"""

    account = serializers.CharField(label="管理员账号")
    password = serializers.CharField(write_only=True, style={"input_type": "password"},
                                     label="密码")


class AdminAuthTokenSerializer(serializers.Serializer):
    """功能说明：组装管理员登录成功后的令牌与资料响应。"""

    @staticmethod
    def build_response(user: User) -> dict:
        """功能说明：生成管理员 access token 与用户资料。"""
        access_token = AccessToken.for_user(user)
        return {
            "access": str(access_token),
            "user": AdminUserSerializer(user).data,
        }


class AdminUserSerializer(serializers.ModelSerializer):
    """功能说明：只读输出系统用户资料。"""

    avatar_url = serializers.SerializerMethodField()
    date_joined = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)

    class Meta:
        model = User
        fields = ("id", "username", "mobile", "email", "first_name", "last_name",
                  "role", "is_active", "is_staff", "avatar", "avatar_url", "date_joined")

    def get_avatar_url(self, obj) -> str:
        """功能说明：拼接可访问的头像绝对地址。"""
        if not obj.avatar:
            return ""
        return build_absolute_media_url(obj.avatar.name, self.context.get("request"))


class AdminUserWriteSerializer(serializers.ModelSerializer):
    """功能说明：校验并写入系统用户数据。"""

    password = serializers.CharField(write_only=True, required=False, allow_blank=True,
                                     label="密码")

    class Meta:
        model = User
        fields = ("username", "password", "mobile", "email", "first_name", "last_name",
                  "role", "is_active", "is_staff")

    def validate_mobile(self, value: str) -> str:
        """功能说明：校验手机号格式与唯一性。"""
        mobile = (value or "").strip()
        if not re.fullmatch(r"1[3-9]\d{9}", mobile):
            raise serializers.ValidationError("请输入正确的11位手机号。")
        queryset = User.objects.filter(mobile=mobile)
        if self.instance is not None:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError("该手机号已被其他账号使用。")
        return mobile

    def create(self, validated_data):
        """功能说明：创建用户并处理密码哈希。"""
        password = validated_data.pop("password", "") or ""
        user = User(**validated_data)
        user.set_password(password or "123456")
        user.save()
        return user

    def update(self, instance, validated_data):
        """功能说明：更新用户资料，密码留空时保持原密码。"""
        password = validated_data.pop("password", "")
        for field, value in validated_data.items():
            setattr(instance, field, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class AdminRoomTypeSerializer(serializers.ModelSerializer):
    """功能说明：只读输出房型资料并拼接封面图绝对地址。"""

    cover_image = serializers.SerializerMethodField()

    class Meta:
        model = RoomType
        fields = ("id", "name", "price", "capacity", "area", "bed_type", "window",
                  "breakfast", "description", "cover_image", "total_stock",
                  "remaining_stock")

    def get_cover_image(self, obj) -> str:
        """功能说明：把封面图相对路径转换为绝对 URL。"""
        return build_absolute_media_url(obj.cover_image, self.context.get("request"))


class AdminRoomTypeWriteSerializer(serializers.ModelSerializer):
    """功能说明：校验并写入房型数据，支持直接上传封面图片。"""

    cover_image_upload = serializers.FileField(write_only=True, required=False,
                                               allow_null=True, label="封面图片")

    class Meta:
        model = RoomType
        fields = ("name", "price", "capacity", "area", "bed_type", "window", "breakfast",
                  "description", "cover_image_upload", "total_stock", "remaining_stock")

    def _save_cover_image(self, uploaded_file) -> str:
        """功能说明：保存上传的封面图片并返回相对路径。"""
        suffix = Path(uploaded_file.name).suffix.lower() or ".jpg"
        storage_name = f"rooms/cover_{uploaded_file.name}"
        saved_name = MEDIA_STORAGE.save(storage_name, uploaded_file)
        return saved_name.replace("\\", "/")

    def _apply_cover(self, instance, uploaded_file):
        """功能说明：把上传文件落盘并写回房型封面字段。"""
        if uploaded_file is None:
            return instance
        instance.cover_image = self._save_cover_image(uploaded_file)
        instance.save(update_fields=["cover_image"])
        return instance

    def create(self, validated_data):
        """功能说明：创建房型并保存封面图片。"""
        uploaded_file = validated_data.pop("cover_image_upload", None)
        instance = RoomType.objects.create(**validated_data)
        return self._apply_cover(instance, uploaded_file)

    def update(self, instance, validated_data):
        """功能说明：更新房型并可选替换封面图片。"""
        uploaded_file = validated_data.pop("cover_image_upload", None)
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()
        return self._apply_cover(instance, uploaded_file)


class AdminRoomSerializer(serializers.ModelSerializer):
    """功能说明：只读输出实体房间信息。"""

    room_type_name = serializers.CharField(source="room_type.name", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Room
        fields = ("id", "room_number", "room_type", "room_type_name", "floor",
                  "status", "status_display")


class AdminRoomWriteSerializer(serializers.ModelSerializer):
    """功能说明：校验并写入实体房间数据。"""

    class Meta:
        model = Room
        fields = ("room_number", "room_type", "floor", "status")


class AdminBookingSerializer(serializers.ModelSerializer):
    """功能说明：只读输出订单数据。"""

    username = serializers.CharField(source="user.username", read_only=True)
    room_type_name = serializers.CharField(source="room_type.name", read_only=True)
    room_number = serializers.CharField(source="room.room_number", read_only=True,
                                        allow_null=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)

    class Meta:
        model = Booking
        fields = ("id", "user", "username", "room_type", "room_type_name", "room",
                  "room_number", "start_date", "end_date", "total_price", "status",
                  "status_display", "contact_name", "contact_phone", "id_card",
                  "payment_method", "created_at")


class AdminBookingWriteSerializer(serializers.ModelSerializer):
    """功能说明：校验并写入订单数据。"""

    class Meta:
        model = Booking
        fields = ("user", "room_type", "room", "start_date", "end_date", "total_price",
                  "status", "contact_name", "contact_phone", "id_card", "payment_method")

    def validate(self, attrs):
        """功能说明：校验订单日期的先后关系。"""
        start_date = attrs.get("start_date") or getattr(self.instance, "start_date", None)
        end_date = attrs.get("end_date") or getattr(self.instance, "end_date", None)
        if start_date and end_date and start_date >= end_date:
            raise serializers.ValidationError({"end_date": "退房日期必须晚于入住日期。"})
        return attrs


class AdminFeedbackSerializer(serializers.ModelSerializer):
    """功能说明：只读输出留言反馈数据。"""

    username = serializers.CharField(source="user.username", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)

    class Meta:
        model = Feedback
        fields = ("id", "user", "username", "title", "content", "contact", "status",
                  "status_display", "reply_content", "created_at", "replied_at")


class AdminFeedbackWriteSerializer(serializers.ModelSerializer):
    """功能说明：校验并写入留言反馈数据。"""

    class Meta:
        model = Feedback
        fields = ("user", "title", "content", "contact", "status", "reply_content")


class AdminReviewSerializer(serializers.ModelSerializer):
    """功能说明：只读输出评论数据。"""

    username = serializers.CharField(source="user.username", read_only=True)
    room_type_name = serializers.CharField(source="room_type.name", read_only=True)
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)

    class Meta:
        model = Review
        fields = ("id", "user", "username", "room_type", "room_type_name", "rating",
                  "content", "created_at")


class AdminReviewWriteSerializer(serializers.ModelSerializer):
    """功能说明：校验并写入评论数据。"""

    class Meta:
        model = Review
        fields = ("user", "room_type", "rating", "content")

    def validate_rating(self, value: int) -> int:
        """功能说明：限制评分范围在 1 到 5 之间。"""
        if value is None or value < 1 or value > 5:
            raise serializers.ValidationError("评分必须是 1 到 5 之间的整数。")
        return value


class AdminFavoriteSerializer(serializers.ModelSerializer):
    """功能说明：只读输出收藏数据。"""

    username = serializers.CharField(source="user.username", read_only=True)
    room_type_name = serializers.CharField(source="room_type.name", read_only=True)
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)

    class Meta:
        model = Favorite
        fields = ("id", "user", "username", "room_type", "room_type_name", "created_at")


class AdminFavoriteWriteSerializer(serializers.ModelSerializer):
    """功能说明：校验并写入收藏数据。"""

    class Meta:
        model = Favorite
        fields = ("user", "room_type")
