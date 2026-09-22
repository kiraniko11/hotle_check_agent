"""功能说明：账号模块的序列化器。"""
import re

from django.contrib.auth import authenticate
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import AccessToken

from .models import User


class RegisterSerializer(serializers.Serializer):
    """功能说明：校验普通用户注册参数并创建账号。"""

    username = serializers.CharField(max_length=150, label="用户名")
    mobile = serializers.CharField(max_length=11, label="手机号")
    password = serializers.CharField(write_only=True, label="密码",
                                     style={"input_type": "password"})
    confirm_password = serializers.CharField(write_only=True, label="确认密码",
                                             style={"input_type": "password"})

    def validate_username(self, value: str) -> str:
        """功能说明：校验用户名唯一性。"""
        username = value.strip()
        if User.objects.filter(username=username).exists():
            raise serializers.ValidationError("该用户名已被注册。")
        return username

    def validate_mobile(self, value: str) -> str:
        """功能说明：校验手机号格式与唯一性。"""
        mobile = value.strip()
        if not re.fullmatch(r"1[3-9]\d{9}", mobile):
            raise serializers.ValidationError("请输入正确的手机号。")
        if User.objects.filter(mobile=mobile).exists():
            raise serializers.ValidationError("该手机号已被注册。")
        return mobile

    def validate(self, attrs):
        """功能说明：校验注册密码一致性和长度。"""
        if attrs["password"] != attrs["confirm_password"]:
            raise serializers.ValidationError({"confirm_password": "两次输入的密码不一致。"})
        if len(attrs["password"]) < 6:
            raise serializers.ValidationError({"password": "密码长度至少为 6 个字符。"})
        return attrs

    def create(self, validated_data):
        """功能说明：创建普通用户账号。"""
        validated_data.pop("confirm_password")
        # 使用 Django 用户创建方法写入加密后的密码。
        return User.objects.create_user(
            username=validated_data["username"],
            mobile=validated_data["mobile"],
            password=validated_data["password"],
            role=User.Role.USER,
        )


class LoginSerializer(serializers.Serializer):
    """功能说明：清理用户登录入参。"""

    account = serializers.CharField()
    password = serializers.CharField(write_only=True, style={"input_type": "password"})


class UserProfileSerializer(serializers.ModelSerializer):
    """功能说明：只读输出当前登录用户的个人资料。"""

    avatar = serializers.SerializerMethodField()
    avatar_url = serializers.SerializerMethodField()
    date_joined = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)

    class Meta:
        model = User
        fields = ["id", "username", "mobile", "email", "first_name", "last_name",
                  "avatar", "avatar_url", "role", "date_joined"]

    def get_avatar(self, obj) -> str:
        """功能说明：拼接头像可访问的绝对地址。"""
        if not obj.avatar:
            return ""
        request = self.context.get("request")
        if request is not None:
            return request.build_absolute_uri(obj.avatar.url)
        return obj.avatar.url

    def get_avatar_url(self, obj) -> str:
        """功能说明：兼容前端 avatar_url 命名的头像地址字段。"""
        return self.get_avatar(obj)


class UpdateProfileSerializer(serializers.ModelSerializer):
    """功能说明：校验并更新用户的可编辑个人资料字段。"""

    AVATAR_MAX_SIZE = 2 * 1024 * 1024
    AVATAR_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}

    class Meta:
        model = User
        fields = ("first_name", "last_name", "email", "mobile", "avatar")
        extra_kwargs = {
            "first_name": {"required": False},
            "last_name": {"required": False},
            "email": {"required": False},
            "mobile": {"required": False},
        }

    def validate_avatar(self, value):
        """功能说明：校验上传头像的大小和图片类型。"""
        if value is None or not hasattr(value, "size"):
            return value
        if value.size > self.AVATAR_MAX_SIZE:
            raise serializers.ValidationError("头像大小不能超过 2MB。")
        content_type = getattr(value, "content_type", "")
        if content_type not in self.AVATAR_CONTENT_TYPES:
            raise serializers.ValidationError("仅支持 JPG、PNG、WEBP 或 GIF 图片。")
        return value

    def validate_mobile(self, value: str) -> str:
        """功能说明：校验新手机号的格式与唯一性。"""
        mobile = value.strip()
        if not re.fullmatch(r"1[3-9]\d{9}", mobile):
            raise serializers.ValidationError("请输入正确的11位手机号。")
        # 排除当前用户自身，检查手机号唯一性。
        user = self.context["request"].user
        if User.objects.filter(mobile=mobile).exclude(pk=user.pk).exists():
            raise serializers.ValidationError("该手机号已被其他账号使用。")
        return mobile


class ChangePasswordSerializer(serializers.Serializer):
    """功能说明：校验密码修改请求。"""

    old_password = serializers.CharField(write_only=True, label="原密码",
                                         style={"input_type": "password"})
    new_password = serializers.CharField(write_only=True, label="新密码",
                                         style={"input_type": "password"})
    confirm_password = serializers.CharField(write_only=True, label="确认新密码",
                                             style={"input_type": "password"})

    def validate_old_password(self, value: str) -> str:
        """功能说明：校验原密码是否正确。"""
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("原密码不正确。")
        return value

    def validate(self, attrs):
        """功能说明：校验两次新密码是否一致及长度要求。"""
        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError({"confirm_password": "两次输入的新密码不一致。"})
        if len(attrs["new_password"]) < 6:
            raise serializers.ValidationError({"new_password": "新密码长度至少为 6 个字符。"})
        return attrs


class AuthTokenSerializer(serializers.Serializer):
    """功能说明：组装登录和注册成功后的响应数据。"""

    @staticmethod
    def build_response(user, request=None) -> dict:
        """功能说明：生成 access token 和用户资料响应。"""
        # 签发 SimpleJWT access token。
        access_token = AccessToken.for_user(user)
        serializer = UserProfileSerializer(
            user, context={"request": request} if request else {})
        return {
            "access": str(access_token),
            "user": serializer.data,
        }
