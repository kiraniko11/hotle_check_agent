"""功能说明：账号模块的接口视图。"""
from django.contrib.auth import authenticate
from django.db.models import Q
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import User
from .serializers import (
    AuthTokenSerializer,
    ChangePasswordSerializer,
    LoginSerializer,
    RegisterSerializer,
    UpdateProfileSerializer,
    UserProfileSerializer,
)


class RegisterAPIView(APIView):
    """功能说明：处理普通用户注册请求。"""

    permission_classes = (AllowAny,)

    def post(self, request: Request) -> Response:
        """功能说明：创建用户并签发登录令牌，实现注册即登录。"""
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        response_data = AuthTokenSerializer.build_response(user, request)
        return Response(response_data, status=status.HTTP_201_CREATED)


class LoginAPIView(APIView):
    """功能说明：处理普通用户登录请求。"""

    permission_classes = (AllowAny,)

    def post(self, request: Request) -> Response:
        """功能说明：校验账号密码并返回登录令牌。"""
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # 根据用户名或手机号查找用户记录。
        account = serializer.validated_data["account"]
        user = User.objects.filter(Q(username=account) | Q(mobile=account)).first()
        if user is None:
            raise AuthenticationFailed("账号或密码错误。")

        # 使用 Django 认证系统校验密码和账号状态。
        authenticated_user = authenticate(
            username=user.username,
            password=serializer.validated_data["password"],
        )
        if authenticated_user is None:
            raise AuthenticationFailed("账号或密码错误。")

        response_data = AuthTokenSerializer.build_response(authenticated_user, request)
        return Response(response_data, status=status.HTTP_200_OK)


class ProfileAPIView(APIView):
    """功能说明：获取或更新当前登录用户的个人资料。"""

    permission_classes = (IsAuthenticated,)

    def get(self, request: Request) -> Response:
        """功能说明：获取用户资料。"""
        serializer = UserProfileSerializer(request.user, context={"request": request})
        return Response(serializer.data)

    def patch(self, request: Request) -> Response:
        """功能说明：更新用户资料并支持头像上传。"""
        serializer = UpdateProfileSerializer(
            request.user, data=request.data, partial=True,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserProfileSerializer(user, context={"request": request}).data)


class ChangePasswordAPIView(APIView):
    """功能说明：处理当前登录用户的密码修改请求。"""

    permission_classes = (IsAuthenticated,)

    def post(self, request: Request) -> Response:
        """功能说明：校验旧密码并设置新密码。"""
        serializer = ChangePasswordSerializer(data=request.data,
                                             context={"request": request})
        serializer.is_valid(raise_exception=True)
        # 设置新密码并保存，Django 会自动进行哈希处理。
        request.user.set_password(serializer.validated_data["new_password"])
        request.user.save(update_fields=["password"])
        return Response({"code": 200, "msg": "密码修改成功，请使用新密码重新登录。"})


class LogoutAPIView(APIView):
    """功能说明：处理用户退出登录请求。"""

    permission_classes = (IsAuthenticated,)

    def post(self, request: Request) -> Response:
        """功能说明：退出登录，前端负责清理本地令牌。

        项目采用无状态 JWT，服务端无需销毁令牌，仅返回成功标记。
        """
        return Response({"code": 200, "msg": "已退出登录"})
