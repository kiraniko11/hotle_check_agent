"""功能说明：客房业务的对外接口视图。"""

from datetime import date, datetime

from django.db import transaction
from django.db.models import Avg, Count, Q, Sum
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from common.utils import unified_response

from .models import Booking, Favorite, Review, Room, RoomType
from .serializers import (
    BookingSerializer,
    FavoriteSerializer,
    ReviewSerializer,
    RoomTypeSerializer,
)


class RoomTypeListView(APIView):
    """功能说明：列出全部房间类型，并提供简单的参数条件筛选。"""

    permission_classes = (AllowAny,)

    def get(self, request: Request) -> Response:
        """功能说明：获取房型列表信息。"""
        # 获取可选的筛选参数。
        capacity = request.query_params.get("capacity")
        window = request.query_params.get("window")
        breakfast = request.query_params.get("breakfast")

        # 构造查询集。
        queryset = RoomType.objects.all().order_by("price")

        # 按照可容纳人数筛选。
        if capacity:
            queryset = queryset.filter(capacity__gte=int(capacity))

        # 按照是否有窗筛选。
        if window is not None and window != "":
            is_window = window.lower() in ("true", "1", "yes")
            queryset = queryset.filter(window=is_window)

        # 按照是否含早筛选。
        if breakfast is not None and breakfast != "":
            is_breakfast = breakfast.lower() in ("true", "1", "yes")
            queryset = queryset.filter(breakfast=is_breakfast)

        # 注入 request 上下文，使序列化器可以把封面图相对路径拼成绝对 URL。
        serializer = RoomTypeSerializer(queryset, many=True, context={"request": request})
        return unified_response(code=200, msg="获取房型列表成功", data=serializer.data)


class RoomTypeDetailView(APIView):
    """功能说明：获取指定房型的详细信息，包含全部物理房间。"""

    permission_classes = (AllowAny,)

    def get(self, request: Request, pk: int) -> Response:
        """功能说明：查询单个房型详情。"""
        room_type = RoomType.objects.filter(pk=pk).first()
        if room_type is None:
            return unified_response(code=404, msg="未找到指定的房间类型")

        serializer = RoomTypeSerializer(room_type, context={"request": request})
        return unified_response(code=200, msg="获取房型详情成功", data=serializer.data)


class RoomStatsView(APIView):
    """功能说明：使用聚合查询为前端图表准备统计数据。"""

    permission_classes = (AllowAny,)

    def get(self, request: Request) -> Response:
        """功能说明：统计房型、客房与订单的关键指标。"""
        # 房型与客房的整体聚合数据。
        type_aggregate = RoomType.objects.aggregate(
            type_count=Count("id"),
            avg_price=Avg("price"),
            total_stock=Sum("total_stock"),
            remaining_stock=Sum("remaining_stock"),
        )
        room_count = Room.objects.count()
        vacant_count = Room.objects.filter(status=Room.Status.VACANT).count()

        # 各房型的库存分布，用于柱状图展示。
        type_distribution = list(
            RoomType.objects.values("name", "total_stock", "remaining_stock").order_by("price")
        )

        # 订单状态分布，用于饼图展示。
        status_distribution = list(
            Booking.objects.values("status").annotate(count=Count("id")).order_by("status")
        )
        status_labels = dict(Booking.Status.choices)
        for item in status_distribution:
            item["status_display"] = status_labels.get(item["status"], item["status"])

        # 各房型的累计成交金额，用于营收排行。
        revenue_ranking = list(
            Booking.objects.exclude(status=Booking.Status.CANCELLED)
            .values("room_type__name")
            .annotate(revenue=Sum("total_price"), orders=Count("id"))
            .order_by("-revenue")[:8]
        )

        total_revenue = Booking.objects.exclude(status=Booking.Status.CANCELLED).aggregate(
            total=Sum("total_price")
        )["total"] or 0

        data = {
            "room_type_count": type_aggregate["type_count"] or 0,
            "room_count": room_count,
            "total_stock": type_aggregate["total_stock"] or 0,
            "remaining_stock": type_aggregate["remaining_stock"] or 0,
            "vacant_room_count": vacant_count,
            "average_price": round(float(type_aggregate["avg_price"] or 0), 2),
            "booking_count": Booking.objects.count(),
            "review_count": Review.objects.count(),
            "favorite_count": Favorite.objects.count(),
            "total_revenue": float(total_revenue),
            "type_distribution": type_distribution,
            "status_distribution": status_distribution,
            "revenue_ranking": revenue_ranking,
        }
        return unified_response(code=200, msg="获取统计数据成功", data=data)


class FavoriteToggleView(APIView):
    """功能说明：切换普通用户对特定房型的收藏状态。"""

    permission_classes = (IsAuthenticated,)

    def post(self, request: Request, pk: int) -> Response:
        """功能说明：执行收藏或取消收藏的操作。"""
        room_type = RoomType.objects.filter(pk=pk).first()
        if room_type is None:
            return unified_response(code=404, msg="未找到指定的房间类型")

        # 判断是否已存在收藏记录，有则删除、无则创建。
        fav = Favorite.objects.filter(user=request.user, room_type=room_type).first()
        if fav is not None:
            fav.delete()
            return unified_response(code=200, msg="取消收藏成功", data={"is_favorite": False})

        Favorite.objects.create(user=request.user, room_type=room_type)
        return unified_response(code=200, msg="添加收藏成功", data={"is_favorite": True})


class FavoriteStatusView(APIView):
    """功能说明：查询当前登录用户对特定房型的收藏状态。"""

    permission_classes = (IsAuthenticated,)

    def get(self, request: Request, pk: int) -> Response:
        """功能说明：返回收藏状态标记。"""
        is_favorite = Favorite.objects.filter(user=request.user, room_type_id=pk).exists()
        return unified_response(code=200, msg="获取收藏状态成功",
                                data={"is_favorite": is_favorite})


class UserFavoriteListView(APIView):
    """功能说明：列出当前登录用户收藏的全部房型记录。"""

    permission_classes = (IsAuthenticated,)

    def get(self, request: Request) -> Response:
        """功能说明：获取收藏列表。"""
        favorites = Favorite.objects.filter(user=request.user).select_related("room_type")
        serializer = FavoriteSerializer(favorites, many=True, context={"request": request})
        return unified_response(code=200, msg="获取收藏列表成功", data=serializer.data)


class BookingCreateView(APIView):
    """功能说明：处理普通用户预订房间的创建请求。"""

    permission_classes = (IsAuthenticated,)

    def post(self, request: Request, pk: int) -> Response:
        """功能说明：创建新的客房预订订单。"""
        room_type = RoomType.objects.filter(pk=pk).first()
        if room_type is None:
            return unified_response(code=404, msg="未找到指定的房间类型")

        start_date_str = request.data.get("start_date")
        end_date_str = request.data.get("end_date")
        if not start_date_str or not end_date_str:
            return unified_response(code=400, msg="入住日期与离店日期不能为空")

        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        except ValueError:
            return unified_response(code=400, msg="日期格式解析失败，请使用 YYYY-MM-DD 格式")

        # 日期合法性校验。
        if start_date >= end_date:
            return unified_response(code=400, msg="入住日期必须早于退房日期")
        if start_date < date.today():
            return unified_response(code=400, msg="入住日期不能早于当前日期")

        contact_name = request.data.get("contact_name", "")
        contact_phone = request.data.get("contact_phone", "")
        id_card = request.data.get("id_card", "")
        payment_method = request.data.get("payment_method", "hang_charge")

        # 核心库存分配与事务逻辑。
        try:
            with transaction.atomic():
                # 重新锁表查询房型，确保高并发下的库存一致性。
                rt = RoomType.objects.select_for_update().filter(pk=pk).first()
                if rt.remaining_stock <= 0:
                    return unified_response(code=400, msg="该房型当前可用客房库存不足")

                # 寻找一间空闲的物理房间。
                room = Room.objects.select_for_update().filter(
                    room_type=rt, status=Room.Status.VACANT).first()
                if room is None:
                    return unified_response(code=400, msg="未找到可供分配的空闲物理客房")

                # 更新物理房间状态为已入住，减少房型可用库存。
                room.status = Room.Status.OCCUPIED
                room.save(update_fields=["status"])
                rt.remaining_stock -= 1
                rt.save(update_fields=["remaining_stock"])

                # 计算预订的总天数及总房费。
                stay_days = (end_date - start_date).days
                total_price = rt.price * stay_days

                booking = Booking.objects.create(
                    user=request.user, room_type=rt, room=room,
                    start_date=start_date, end_date=end_date,
                    total_price=total_price, contact_name=contact_name,
                    contact_phone=contact_phone, id_card=id_card,
                    payment_method=payment_method, status=Booking.Status.BOOKED,
                )

                serializer = BookingSerializer(booking)
                return unified_response(code=200, msg="房间预订成功", data=serializer.data)
        except Exception as err:
            return unified_response(code=500, msg=f"服务器执行预订异常: {err}")


class UserBookingListView(APIView):
    """功能说明：列出当前登录用户名下的全部预订订单。"""

    permission_classes = (IsAuthenticated,)

    def get(self, request: Request) -> Response:
        """功能说明：获取名下订单的序列化集合。"""
        bookings = Booking.objects.filter(user=request.user).select_related(
            "room_type", "room").order_by("-created_at")
        serializer = BookingSerializer(bookings, many=True)
        return unified_response(code=200, msg="获取预订订单列表成功", data=serializer.data)


class BookingCancelView(APIView):
    """功能说明：允许宾客对已预订未出行的行程执行取消预订操作，释放资源。"""

    permission_classes = (IsAuthenticated,)

    def post(self, request: Request, pk: int) -> Response:
        """功能说明：取消特定预订订单，并退回房源库存与清空物理房间占用。"""
        try:
            with transaction.atomic():
                # 加上悲观锁查询该订单记录，防止多并发状态冲突。
                booking = Booking.objects.select_for_update().filter(
                    pk=pk, user=request.user).first()
                if booking is None:
                    return unified_response(code=404, msg="未找到指定的预订行程订单")

                # 只有 booked 状态的订单才可以取消。
                if booking.status != Booking.Status.BOOKED:
                    return unified_response(
                        code=400,
                        msg=f"该行程状态为【{booking.get_status_display()}】，不支持执行取消操作",
                    )

                # 将订单状态更新为已取消。
                booking.status = Booking.Status.CANCELLED
                booking.save(update_fields=["status"])

                # 如果已经分配了具体的物理房间，将该房间的状态释放为 vacant。
                if booking.room_id:
                    room = Room.objects.select_for_update().filter(pk=booking.room_id).first()
                    if room is not None:
                        room.status = Room.Status.VACANT
                        room.save(update_fields=["status"])

                # 恢复该房型的可用库存数量。
                room_type = RoomType.objects.select_for_update().filter(
                    pk=booking.room_type_id).first()
                if room_type is not None:
                    room_type.remaining_stock += 1
                    room_type.save(update_fields=["remaining_stock"])

                return unified_response(code=200, msg="行程预订已成功取消，房源库存已恢复")
        except Exception as err:
            return unified_response(code=500, msg=f"服务器执行取消行程异常: {err}")


class ReviewListCreateView(APIView):
    """功能说明：获取客房评价列表或为已预订宾客提供评价发表功能。"""

    def get_permissions(self):
        """功能说明：动态配置权限，GET 允许匿名，POST 须鉴权。"""
        if self.request.method == "POST":
            return [IsAuthenticated()]
        return [AllowAny()]

    def get(self, request: Request, pk: int) -> Response:
        """功能说明：获取某房型下的全部历史评语。"""
        room_type = RoomType.objects.filter(pk=pk).first()
        if room_type is None:
            return unified_response(code=404, msg="未找到指定的房间类型")

        reviews = Review.objects.filter(room_type=room_type).select_related("user")
        serializer = ReviewSerializer(reviews, many=True, context={"request": request})
        return unified_response(code=200, msg="获取评价列表成功", data=serializer.data)

    def post(self, request: Request, pk: int) -> Response:
        """功能说明：为预订过的宾客提交新的文字与打星评价。"""
        room_type = RoomType.objects.filter(pk=pk).first()
        if room_type is None:
            return unified_response(code=404, msg="未找到指定的房间类型")

        # 校验预订凭证：要求宾客必须真实预订过本房型，且非取消状态。
        has_booked = Booking.objects.filter(
            user=request.user, room_type=room_type
        ).exclude(status=Booking.Status.CANCELLED).exists()
        if not has_booked:
            return unified_response(code=403, msg="只有真实预订并体验过该客房的宾客才能发表评价")

        rating = request.data.get("rating")
        content = request.data.get("content")
        if rating is None or not content:
            return unified_response(code=400, msg="评分等级与评语内容不能为空")

        try:
            rating_val = int(rating)
            if rating_val < 1 or rating_val > 5:
                raise ValueError()
        except (TypeError, ValueError):
            return unified_response(code=400, msg="评分必须是 1 到 5 之间的整数")

        # 创建并保存评语。
        review = Review.objects.create(
            user=request.user, room_type=room_type,
            rating=rating_val, content=content,
        )
        serializer = ReviewSerializer(review, context={"request": request})
        return unified_response(code=200, msg="评价发表成功", data=serializer.data)


class ReviewEligibilityView(APIView):
    """功能说明：判断当前登录用户是否具备对指定房型的评价资格。"""

    permission_classes = (IsAuthenticated,)

    def get(self, request: Request, pk: int) -> Response:
        """功能说明：返回评价资格标记与已发表的评价数量。"""
        eligible = Booking.objects.filter(
            user=request.user, room_type_id=pk
        ).exclude(status=Booking.Status.CANCELLED).exists()
        reviewed = Review.objects.filter(user=request.user, room_type_id=pk).exists()
        return unified_response(code=200, msg="获取评价资格成功",
                                data={"eligible": eligible, "reviewed": reviewed})


class ReviewBoardView(APIView):
    """功能说明：酒店评论区看板，提供全店评价列表、评分汇总与发表评价。"""

    def get_permissions(self):
        """功能说明：GET 允许匿名浏览，POST 须登录后发表。"""
        if self.request.method == "POST":
            return [IsAuthenticated()]
        return [AllowAny()]

    def get(self, request: Request) -> Response:
        """功能说明：返回全部房型评价、评分汇总与可选择的房型列表。"""
        reviews = Review.objects.select_related("user", "room_type")
        serializer = ReviewSerializer(reviews, many=True, context={"request": request})

        aggregate = reviews.aggregate(average=Avg("rating"), total=Count("id"))
        average = round(aggregate["average"] or 0, 1)

        # 统计 1-5 星各自的数量，用于前端展示评分分布。
        distribution_rows = (
            Review.objects.values("rating").annotate(count=Count("id")).order_by("rating")
        )
        distribution = {str(row["rating"]): row["count"] for row in distribution_rows}

        room_types = RoomType.objects.values("id", "name").order_by("id")

        return unified_response(code=200, msg="获取酒店评价看板成功", data={
            "summary": {
                "average": average,
                "total": aggregate["total"] or 0,
                "distribution": distribution,
            },
            "reviews": serializer.data,
            "room_types": list(room_types),
        })

    def post(self, request: Request) -> Response:
        """功能说明：登录用户选择房型并发表评分与文字评价。"""
        room_type_id = request.data.get("room_type")
        rating = request.data.get("rating")
        content = (request.data.get("content") or "").strip()

        room_type = RoomType.objects.filter(pk=room_type_id).first()
        if room_type is None:
            return unified_response(code=400, msg="请选择要评价的房型")

        try:
            rating_val = int(rating)
            if rating_val < 1 or rating_val > 5:
                raise ValueError()
        except (TypeError, ValueError):
            return unified_response(code=400, msg="评分必须是 1 到 5 之间的整数")

        if len(content) < 5:
            return unified_response(code=400, msg="评价内容至少 5 个字")
        if len(content) > 500:
            return unified_response(code=400, msg="评价内容不能超过 500 字")

        review = Review.objects.create(
            user=request.user, room_type=room_type,
            rating=rating_val, content=content,
        )
        serializer = ReviewSerializer(review, context={"request": request})
        return unified_response(code=200, msg="评价发表成功", data=serializer.data)
