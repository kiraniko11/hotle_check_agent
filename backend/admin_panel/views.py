"""功能说明：管理后台的接口视图。"""

from typing import Any

from django.contrib.auth import authenticate
from django.db import transaction
from django.db.models import Count, Q, QuerySet, Sum
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User
from common.utils import admin_response
from feedback.models import Feedback
from rooms.models import Booking, Favorite, Review, Room, RoomType

from .permissions import IsSystemAdmin
from .serializers import (
    AdminAuthTokenSerializer,
    AdminBookingSerializer,
    AdminBookingWriteSerializer,
    AdminFavoriteSerializer,
    AdminFavoriteWriteSerializer,
    AdminFeedbackSerializer,
    AdminFeedbackWriteSerializer,
    AdminLoginSerializer,
    AdminReviewSerializer,
    AdminReviewWriteSerializer,
    AdminRoomSerializer,
    AdminRoomTypeSerializer,
    AdminRoomTypeWriteSerializer,
    AdminRoomWriteSerializer,
    AdminUserSerializer,
    AdminUserWriteSerializer,
)
from .services import adjust_room_type_stock, get_remaining_delta_for_status


class AdminLoginAPIView(APIView):
    """功能说明：处理系统管理员专属登录请求。"""

    permission_classes = (AllowAny,)

    def post(self, request: Request) -> Response:
        """功能说明：校验管理员账号密码并签发令牌。"""
        serializer = AdminLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # 支持使用用户名或手机号登录管理员后台。
        account = serializer.validated_data["account"]
        user = User.objects.filter(Q(username=account) | Q(mobile=account)).first()
        if user is None:
            raise AuthenticationFailed("管理员账号或密码错误。")

        authenticated_user = authenticate(
            username=user.username,
            password=serializer.validated_data["password"],
        )
        if authenticated_user is None:
            raise AuthenticationFailed("管理员账号或密码错误。")

        # 管理后台只允许 admin 角色登录。
        if authenticated_user.role != User.Role.ADMIN:
            raise PermissionDenied("当前账号不是系统管理员。")

        response_data = AdminAuthTokenSerializer.build_response(authenticated_user)
        return admin_response(code=200, msg="管理员登录成功", data=response_data)


class AdminProfileAPIView(APIView):
    """功能说明：返回当前登录管理员的资料。"""

    permission_classes = (IsSystemAdmin,)

    def get(self, request: Request) -> Response:
        """功能说明：获取管理员个人资料。"""
        serializer = AdminUserSerializer(request.user, context={"request": request})
        return admin_response(code=200, msg="获取管理员资料成功", data=serializer.data)


class AdminStatsAPIView(APIView):
    """功能说明：返回管理后台的全局统计指标。"""

    permission_classes = (IsSystemAdmin,)

    def get(self, request: Request) -> Response:
        """功能说明：统计用户、房型、房间、订单等关键数量。"""
        data = {
            "users": User.objects.count(),
            "admins": User.objects.filter(role=User.Role.ADMIN).count(),
            "room_types": RoomType.objects.count(),
            "rooms": Room.objects.count(),
            "vacant_rooms": Room.objects.filter(status=Room.Status.VACANT).count(),
            "bookings": Booking.objects.count(),
            "pending_bookings": Booking.objects.filter(status=Booking.Status.BOOKED).count(),
            "feedbacks": Feedback.objects.count(),
            "pending_feedbacks": Feedback.objects.filter(
                status=Feedback.Status.PENDING).count(),
            "reviews": Review.objects.count(),
            "favorites": Favorite.objects.count(),
            "revenue": float(
                Booking.objects.exclude(status=Booking.Status.CANCELLED).aggregate(
                    total=Sum("total_price"))["total"] or 0
            ),
        }
        return admin_response(code=200, msg="获取统计数据成功", data=data)


class BaseAdminResourceAPIView(APIView):
    """功能说明：提供管理后台通用资源增删改查能力。"""

    permission_classes = (IsSystemAdmin,)
    model = None
    serializer_class = None
    write_serializer_class = None
    search_fields: tuple[str, ...] = ()
    ordering = "-id"
    select_related_fields: tuple[str, ...] = ()

    def get_serializer_class(self):
        """功能说明：获取当前资源使用的序列化器类。"""
        # 写入序列化器未单独指定时复用读取序列化器。
        return self.serializer_class

    def get_write_serializer_class(self):
        """功能说明：获取当前资源写入时使用的序列化器类。"""
        # 写入序列化器未单独指定时复用读取序列化器。
        return self.write_serializer_class or self.serializer_class

    def get_queryset(self, request: Request) -> QuerySet:
        """功能说明：构建当前资源的管理查询集。"""
        # 基于模型构造初始查询集。
        queryset = self.model.objects.all()

        # 按资源配置预加载外键展示字段。
        if self.select_related_fields:
            queryset = queryset.select_related(*self.select_related_fields)

        # 根据关键字执行跨字段模糊搜索。
        keyword = request.query_params.get("keyword", "").strip()
        if keyword and self.search_fields:
            query = Q()
            for field in self.search_fields:
                query |= Q(**{f"{field}__icontains": keyword})
            queryset = queryset.filter(query)

        # 应用默认排序。
        return queryset.order_by(self.ordering)

    def get_object(self, request: Request, pk: int) -> Any:
        """功能说明：根据主键获取管理资源对象。"""
        # 从当前资源查询集中查找指定对象。
        return self.get_queryset(request).filter(pk=pk).first()

    def serialize(self, instance: Any, request: Request) -> dict[str, Any]:
        """功能说明：序列化单个管理资源对象。"""
        # 注入请求上下文，方便头像等媒体字段生成绝对地址。
        serializer = self.get_serializer_class()(instance, context={"request": request})
        return serializer.data

    def list_data(self, request: Request) -> list[dict[str, Any]]:
        """功能说明：序列化当前资源列表。"""
        # 查询并序列化资源列表。
        serializer = self.get_serializer_class()(
            self.get_queryset(request), many=True, context={"request": request})
        return serializer.data

    def get(self, request: Request, pk: int | None = None) -> Response:
        """功能说明：获取资源列表或单个资源详情。"""
        # 未传主键时返回列表数据。
        if pk is None:
            return admin_response(code=200, msg="获取列表成功", data=self.list_data(request))

        # 传入主键时返回详情数据。
        instance = self.get_object(request, pk)
        if instance is None:
            return admin_response(code=404, msg="数据不存在",
                                  status_code=status.HTTP_404_NOT_FOUND)
        return admin_response(code=200, msg="获取详情成功",
                              data=self.serialize(instance, request))

    def post(self, request: Request) -> Response:
        """功能说明：创建新的管理资源。"""
        # 校验前端提交的数据。
        serializer = self.get_write_serializer_class()(
            data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        # 创建资源并返回最新详情。
        instance = serializer.save()
        return admin_response(
            code=201,
            msg="创建成功",
            data=self.serialize(instance, request),
            status_code=status.HTTP_201_CREATED,
        )

    def patch(self, request: Request, pk: int) -> Response:
        """功能说明：更新指定管理资源。"""
        # 查找需要更新的对象。
        instance = self.get_object(request, pk)
        if instance is None:
            return admin_response(code=404, msg="数据不存在",
                                  status_code=status.HTTP_404_NOT_FOUND)

        # 校验并保存局部更新数据。
        serializer = self.get_write_serializer_class()(
            instance, data=request.data, partial=True, context={"request": request})
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        return admin_response(code=200, msg="更新成功",
                              data=self.serialize(instance, request))

    def delete(self, request: Request, pk: int) -> Response:
        """功能说明：删除指定管理资源。"""
        # 查找需要删除的对象。
        instance = self.get_object(request, pk)
        if instance is None:
            return admin_response(code=404, msg="数据不存在",
                                  status_code=status.HTTP_404_NOT_FOUND)

        # 删除对象并返回统一提示。
        instance.delete()
        return admin_response(code=200, msg="删除成功")


class AdminUserAPIView(BaseAdminResourceAPIView):
    """功能说明：提供系统用户管理接口。"""

    model = User
    serializer_class = AdminUserSerializer
    write_serializer_class = AdminUserWriteSerializer
    search_fields = ("username", "mobile", "email", "first_name", "last_name")
    ordering = "-date_joined"

    def delete(self, request: Request, pk: int) -> Response:
        """功能说明：删除指定系统用户并保护当前管理员账号。"""
        if request.user.pk == pk:
            return admin_response(code=400, msg="不能删除当前登录的管理员账号",
                                  status_code=status.HTTP_400_BAD_REQUEST)
        return super().delete(request, pk)


class AdminRoomTypeAPIView(BaseAdminResourceAPIView):
    """功能说明：提供房型管理接口。"""

    model = RoomType
    serializer_class = AdminRoomTypeSerializer
    write_serializer_class = AdminRoomTypeWriteSerializer
    search_fields = ("name", "bed_type", "description")
    ordering = "id"


class AdminRoomAPIView(BaseAdminResourceAPIView):
    """功能说明：提供实体房间管理接口。"""

    model = Room
    serializer_class = AdminRoomSerializer
    write_serializer_class = AdminRoomWriteSerializer
    search_fields = ("room_number", "room_type__name", "status")
    select_related_fields = ("room_type",)
    ordering = "id"

    def post(self, request: Request) -> Response:
        """功能说明：创建实体房间并同步房型库存。"""
        serializer = self.get_write_serializer_class()(
            data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            room = serializer.save()
            adjust_room_type_stock(
                room.room_type_id,
                total_delta=1,
                remaining_delta=get_remaining_delta_for_status(room.status),
            )
        return admin_response(code=201, msg="创建成功",
                              data=self.serialize(room, request),
                              status_code=status.HTTP_201_CREATED)

    def patch(self, request: Request, pk: int) -> Response:
        """功能说明：更新实体房间并同步房型库存。"""
        with transaction.atomic():
            room = Room.objects.select_for_update().filter(pk=pk).first()
            if room is None:
                return admin_response(code=404, msg="数据不存在",
                                      status_code=status.HTTP_404_NOT_FOUND)

            old_room_type_id = room.room_type_id
            old_remaining = get_remaining_delta_for_status(room.status)

            serializer = self.get_write_serializer_class()(
                room, data=request.data, partial=True, context={"request": request})
            serializer.is_valid(raise_exception=True)
            updated_room = serializer.save()

            new_room_type_id = updated_room.room_type_id
            new_remaining = get_remaining_delta_for_status(updated_room.status)
            if old_room_type_id == new_room_type_id:
                adjust_room_type_stock(new_room_type_id,
                                       remaining_delta=new_remaining - old_remaining)
            else:
                adjust_room_type_stock(old_room_type_id, total_delta=-1,
                                       remaining_delta=-old_remaining)
                adjust_room_type_stock(new_room_type_id, total_delta=1,
                                       remaining_delta=new_remaining)

        return admin_response(code=200, msg="更新成功",
                              data=self.serialize(updated_room, request))

    def delete(self, request: Request, pk: int) -> Response:
        """功能说明：删除实体房间并回退房型库存。"""
        with transaction.atomic():
            room = Room.objects.select_for_update().filter(pk=pk).first()
            if room is None:
                return admin_response(code=404, msg="数据不存在",
                                      status_code=status.HTTP_404_NOT_FOUND)

            room_type_id = room.room_type_id
            remaining = get_remaining_delta_for_status(room.status)
            # 房间被订单引用时禁止直接删除，避免历史订单丢失房间信息。
            if room.bookings.exists():
                return admin_response(
                    code=400,
                    msg="该房间已存在关联订单，无法删除。",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

            room.delete()
            adjust_room_type_stock(room_type_id, total_delta=-1, remaining_delta=-remaining)

        return admin_response(code=200, msg="删除成功")


class AdminBookingAPIView(BaseAdminResourceAPIView):
    """功能说明：提供预订订单管理接口。"""

    model = Booking
    serializer_class = AdminBookingSerializer
    write_serializer_class = AdminBookingWriteSerializer
    search_fields = ("user__username", "room_type__name", "contact_name",
                     "contact_phone", "status")
    select_related_fields = ("user", "room_type", "room")
    ordering = "-created_at"


class AdminFeedbackAPIView(BaseAdminResourceAPIView):
    """功能说明：提供用户留言反馈管理接口。"""

    model = Feedback
    serializer_class = AdminFeedbackSerializer
    write_serializer_class = AdminFeedbackWriteSerializer
    search_fields = ("user__username", "title", "content", "contact",
                     "reply_content", "status")
    select_related_fields = ("user",)
    ordering = "-created_at"

    def patch(self, request: Request, pk: int) -> Response:
        """功能说明：更新留言反馈并自动维护回复时间。"""
        feedback = self.get_object(request, pk)
        if feedback is None:
            return admin_response(code=404, msg="数据不存在",
                                  status_code=status.HTTP_404_NOT_FOUND)

        serializer = self.get_write_serializer_class()(
            feedback, data=request.data, partial=True, context={"request": request})
        serializer.is_valid(raise_exception=True)
        updated_feedback = serializer.save()

        # 有回复内容且尚未记录回复时间时自动标记已回复。
        if updated_feedback.reply_content and updated_feedback.replied_at is None:
            updated_feedback.status = Feedback.Status.REPLIED
            updated_feedback.replied_at = timezone.now()
            updated_feedback.save(update_fields=["status", "replied_at"])

        return admin_response(code=200, msg="更新成功",
                              data=self.serialize(updated_feedback, request))


class AdminReviewAPIView(BaseAdminResourceAPIView):
    """功能说明：提供用户评论管理接口。"""

    model = Review
    serializer_class = AdminReviewSerializer
    write_serializer_class = AdminReviewWriteSerializer
    search_fields = ("user__username", "room_type__name", "content")
    select_related_fields = ("user", "room_type")
    ordering = "-created_at"


class AdminFavoriteAPIView(BaseAdminResourceAPIView):
    """功能说明：提供用户收藏管理接口。"""

    model = Favorite
    serializer_class = AdminFavoriteSerializer
    write_serializer_class = AdminFavoriteWriteSerializer
    search_fields = ("user__username", "room_type__name")
    select_related_fields = ("user", "room_type")
    ordering = "-created_at"
