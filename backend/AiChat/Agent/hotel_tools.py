"""功能说明：定义智能体可调用的酒店业务工具集合。"""

from datetime import date

from django.db import transaction
from django.db.models import Q
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from accounts.models import User
from rooms.models import Booking, Favorite, Room, RoomType

from .utils.serializers import (
    _get_user,
    build_json_response,
    build_user_contact_profile,
    parse_date_value,
    serialize_booking,
    serialize_room_type,
)


class EmptyArgs(BaseModel):
    """功能说明：定义无入参工具的占位结构。"""


class SearchRoomTypesArgs(BaseModel):
    """功能说明：定义房型查询工具的入参结构。"""

    capacity: int | None = Field(default=None, description="入住人数下限")
    max_price: float | None = Field(default=None, description="每晚最高预算")
    breakfast: bool | None = Field(default=None, description="是否要求含早餐")
    window: bool | None = Field(default=None, description="是否要求有窗")
    keyword: str | None = Field(default=None, description="房型名称或描述关键词")


class CreateBookingArgs(BaseModel):
    """功能说明：定义创建预订工具的入参结构。"""

    room_type_id: int = Field(description="要预订的房型编号，必须来自房型查询结果")
    start_date: str = Field(description="入住日期，格式 YYYY-MM-DD")
    end_date: str = Field(description="退房日期，格式 YYYY-MM-DD")
    contact_name: str | None = Field(default=None, description="入住人姓名，缺省时使用用户资料")
    contact_phone: str | None = Field(default=None, description="联系电话，缺省时使用用户资料")
    id_card: str = Field(default="", description="入住人身份证号，可选")
    payment_method: str = Field(default="hang_charge", description="支付方式，默认会员挂账")


def _search_room_types(
    user_id: int,
    capacity: int | None = None,
    max_price: float | None = None,
    breakfast: bool | None = None,
    window: bool | None = None,
    keyword: str | None = None,
) -> str:
    """功能说明：根据用户需求和收藏信息查询可推荐房型。"""
    # 查询当前用户，确保收藏标记基于真实用户上下文计算。
    user = _get_user(user_id)

    # 基于可售房型构造查询条件。
    queryset = RoomType.objects.filter(remaining_stock__gt=0)
    if capacity is not None:
        queryset = queryset.filter(capacity__gte=capacity)
    if max_price is not None:
        queryset = queryset.filter(price__lte=max_price)
    if breakfast is not None:
        queryset = queryset.filter(breakfast=breakfast)
    if window is not None:
        queryset = queryset.filter(window=window)
    if keyword:
        queryset = queryset.filter(
            Q(name__icontains=keyword) | Q(description__icontains=keyword)
        )

    # 读取用户收藏房型编号，用于推荐排序和结果标记。
    favorite_ids = set(
        Favorite.objects.filter(user=user).values_list("room_type_id", flat=True)
    ) if user is not None else set()

    # 先按是否收藏排序，再按价格升序排序。
    room_types = sorted(
        queryset[:20],
        key=lambda item: (item.id not in favorite_ids, item.price),
    )
    result = [serialize_room_type(item, item.id in favorite_ids) for item in room_types[:8]]

    if not result:
        return build_json_response({
            "success": True,
            "message": "没有找到符合条件的可预订房型，可建议用户放宽人数、预算或含早要求。",
            "room_types": [],
        })

    # 返回结构化查询结果。
    return build_json_response({
        "success": True,
        "message": f"共查询到 {len(result)} 个可预订房型。",
        "room_types": result,
    })


def _get_user_context(user_id: int) -> str:
    """功能说明：查询当前用户的历史预订和收藏上下文。"""
    # 查询当前用户，确保只返回本人业务数据。
    user = _get_user(user_id)
    if user is None:
        return build_json_response({"success": False, "message": "未找到当前用户。"})

    # 查询最近历史订单，帮助模型理解用户偏好。
    bookings = Booking.objects.filter(user=user).select_related(
        "room_type", "room").order_by("-created_at")[:5]
    booking_data = [serialize_booking(item) for item in bookings]

    # 查询用户收藏房型，帮助模型优先推荐用户关注过的房间。
    favorites = Favorite.objects.filter(user=user).select_related(
        "room_type").order_by("-created_at")[:8]
    favorite_data = [serialize_room_type(item.room_type, True) for item in favorites]

    # 返回结构化用户上下文。
    return build_json_response({
        "success": True,
        "message": "用户上下文查询成功。",
        "profile": build_user_contact_profile(user),
        "history_bookings": booking_data,
        "favorite_room_types": favorite_data,
    })


def _get_user_profile(user_id: int) -> str:
    """功能说明：查询当前用户可用于预订登记的个人资料。"""
    user = _get_user(user_id)
    profile = build_user_contact_profile(user)

    return build_json_response({
        "success": True,
        "message": "用户个人资料查询成功。",
        "profile": profile,
        "can_auto_fill_contact": len(profile["missing_fields"]) == 0,
    })


def _create_booking(
    user_id: int,
    room_type_id: int,
    start_date: str,
    end_date: str,
    contact_name: str | None = None,
    contact_phone: str | None = None,
    id_card: str = "",
    payment_method: str = "hang_charge",
) -> str:
    """功能说明：根据智能体确认后的参数创建房间预订订单。"""
    # 查询当前用户，并读取可自动填充的个人资料。
    user = _get_user(user_id)
    if user is None:
        return build_json_response({"success": False, "message": "未找到当前用户。"})

    profile = build_user_contact_profile(user)

    # 清理实名登记字段，缺失时优先使用用户资料。
    contact_name = (contact_name or "").strip() or profile["contact_name"]
    contact_phone = (contact_phone or "").strip() or profile["contact_phone"]
    id_card = (id_card or "").strip()
    payment_method = (payment_method or "").strip() or "hang_charge"

    # 校验必要登记信息，只有用户资料也缺失时才要求模型追问。
    missing_fields = []
    if not contact_name:
        missing_fields.append("contact_name")
    if not contact_phone:
        missing_fields.append("contact_phone")
    if missing_fields:
        return build_json_response({
            "success": False,
            "message": "用户资料中缺少预订联系人信息，请向用户追问缺失字段。",
            "missing_fields": missing_fields,
            "profile": profile,
        })

    # 解析并校验入住日期区间。
    try:
        parsed_start_date = parse_date_value(start_date, "入住日期")
        parsed_end_date = parse_date_value(end_date, "退房日期")
    except ValueError as exc:
        return build_json_response({"success": False, "message": str(exc)})

    # 校验日期先后关系和当前日期边界。
    if parsed_start_date >= parsed_end_date:
        return build_json_response({"success": False, "message": "入住日期必须早于退房日期。"})
    if parsed_start_date < date.today():
        return build_json_response({"success": False, "message": "入住日期不能早于当前日期。"})

    # 在事务中锁定房型和物理客房，保证库存扣减的一致性。
    try:
        with transaction.atomic():
            room_type = RoomType.objects.select_for_update().filter(pk=room_type_id).first()
            if room_type is None:
                return build_json_response({"success": False, "message": "未找到指定房型。"})
            if room_type.remaining_stock <= 0:
                return build_json_response({"success": False, "message": "该房型当前暂无可预订库存。"})

            # 寻找一间空闲物理客房并锁定，沿用现有预订业务规则。
            room = Room.objects.select_for_update().filter(
                room_type=room_type, status=Room.Status.VACANT).first()
            if room is None:
                return build_json_response({"success": False, "message": "未找到可分配的空闲房间。"})

            # 更新物理房间和房型库存。
            room.status = Room.Status.OCCUPIED
            room.save(update_fields=["status"])
            room_type.remaining_stock -= 1
            room_type.save(update_fields=["remaining_stock"])

            # 计算入住天数和总价。
            stay_days = (parsed_end_date - parsed_start_date).days
            total_price = room_type.price * stay_days

            # 创建订单并返回完整确认信息。
            booking = Booking.objects.create(
                user=user,
                room_type=room_type,
                room=room,
                start_date=parsed_start_date,
                end_date=parsed_end_date,
                total_price=total_price,
                contact_name=contact_name,
                contact_phone=contact_phone,
                id_card=id_card,
                payment_method=payment_method,
                status=Booking.Status.BOOKED,
            )

        # 返回成功下单结果。
        return build_json_response({
            "success": True,
            "message": "房间预订成功。",
            "auto_filled_contact": {
                "contact_name": contact_name == profile["contact_name"],
                "contact_phone": contact_phone == profile["contact_phone"],
            },
            "booking": serialize_booking(booking),
        })
    except Exception as exc:
        # 返回异常信息，避免工具异常中断整段对话。
        return build_json_response({
            "success": False,
            "message": f"创建预订时发生异常：{exc}",
        })


class SearchKnowledgeArgs(BaseModel):
    """功能说明：定义酒店知识检索工具的入参结构。"""

    query: str = Field(description="检索问题或关键词，例如：酒店什么时候成立的、周边有什么文创园")


def search_hotel_knowledge_impl(query: str, top_k: int = 4) -> str:
    """功能说明：从酒店知识向量库中检索与问题相关的资料片段（RAG）。"""
    from .utils.knowledge import search_knowledge

    try:
        return search_knowledge(query, top_k=top_k)
    except Exception as error:  # noqa: BLE001
        return f"知识库检索失败：{error}"


def build_hotel_tools(user_id: int) -> list[StructuredTool]:
    """功能说明：为当前用户构建智能体可调用的酒店业务工具。"""

    # 将当前登录用户编号绑定到工具闭包中，避免模型自行传入或篡改用户身份。
    def search_room_types(capacity=None, max_price=None, breakfast=None,
                          window=None, keyword=None) -> str:
        """功能说明：查询满足入住需求的可预订房型。"""
        return _search_room_types(user_id, capacity, max_price, breakfast, window, keyword)

    def get_user_context() -> str:
        """功能说明：查询当前用户的历史订单和收藏房型。"""
        return _get_user_context(user_id)

    def get_user_profile() -> str:
        """功能说明：查询当前用户的预订联系人资料。"""
        return _get_user_profile(user_id)

    def create_booking(room_type_id, start_date, end_date, contact_name=None,
                       contact_phone=None, id_card="", payment_method="hang_charge") -> str:
        """功能说明：为当前用户创建酒店预订订单，可自动使用用户资料补齐联系人。"""
        return _create_booking(
            user_id=user_id,
            room_type_id=room_type_id,
            start_date=start_date,
            end_date=end_date,
            contact_name=contact_name,
            contact_phone=contact_phone,
            id_card=id_card,
            payment_method=payment_method,
        )

    def search_hotel_knowledge(query, top_k=4) -> str:
        """功能说明：检索酒店介绍、成立历史、周边文创等知识资料（RAG）。"""
        return search_hotel_knowledge_impl(query, top_k)

    # 返回 LangChain StructuredTool 列表，供 LangGraph ToolNode 调用。
    return [
        StructuredTool.from_function(
            func=search_room_types,
            name="search_room_types",
            description=(
                "根据入住人数、预算、早餐、有窗、关键词等条件查询可预订房型，"
                "并标记用户是否收藏。推荐房型前应先调用本工具获取真实房型编号和价格，"
                "调用时只传用户明确提出的条件，未提出的条件不要传。"
            ),
            args_schema=SearchRoomTypesArgs,
        ),
        StructuredTool.from_function(
            func=get_user_context,
            name="get_user_context",
            description="查询当前用户最近历史订单和收藏房型，用于分析偏好与推荐。",
            args_schema=EmptyArgs,
        ),
        StructuredTool.from_function(
            func=get_user_profile,
            name="get_user_profile",
            description=(
                "查询当前用户资料中的入住人姓名和联系电话；创建订单前优先使用此工具，"
                "若返回 can_auto_fill_contact 为 true 则无需再询问用户，资料缺失时才追问。"
            ),
            args_schema=EmptyArgs,
        ),
        StructuredTool.from_function(
            func=create_booking,
            name="create_booking",
            description=(
                "在用户明确确认房型、入住日期和退房日期后创建预订订单；"
                "room_type_id 必须来自 search_room_types 返回的真实房型编号，"
                "日期格式为 YYYY-MM-DD，联系人信息缺失时工具会自动使用用户资料补齐。"
            ),
            args_schema=CreateBookingArgs,
        ),
        StructuredTool.from_function(
            func=search_hotel_knowledge,
            name="search_hotel_knowledge",
            description=(
                "检索酒店知识库（RAG），覆盖酒店介绍、客房设施、成立历史、"
                "周边文创景点、美食推荐等信息。凡是关于酒店背景、历史、周边游玩等"
                "业务数据之外的问题，都应先调用本工具检索资料，再依据检索结果回答。"
            ),
            args_schema=SearchKnowledgeArgs,
        ),
    ]
