"""功能说明：为智能体工具层提供业务对象的序列化与参数解析辅助。"""

from datetime import date, datetime

import json

from accounts.models import User
from rooms.models import Booking, RoomType


def build_json_response(payload: dict) -> str:
    """功能说明：把工具结果序列化为 JSON 字符串返回给大模型。"""
    return json.dumps(payload, ensure_ascii=False, default=str)


def _get_user(user_id: int) -> User | None:
    """功能说明：按编号获取用户对象，供工具闭包内部使用。"""
    return User.objects.filter(pk=user_id).first()


def parse_date_value(value: str, label: str) -> date:
    """功能说明：解析 YYYY-MM-DD 格式的日期字符串。"""
    if not value:
        raise ValueError(f"{label}不能为空。")

    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y年%m月%d日"):
        try:
            return datetime.strptime(str(value).strip(), fmt).date()
        except ValueError:
            continue

    raise ValueError(f"{label}格式无法识别，请使用 YYYY-MM-DD 格式。")


def build_user_contact_profile(user: User | None) -> dict:
    """功能说明：整理用户可用于预订登记的联系人资料。"""
    if user is None:
        return {"contact_name": "", "contact_phone": "", "missing_fields":
                ["contact_name", "contact_phone"]}

    # 优先使用真实姓名，其次退回用户名，保证工具可自动补齐登记信息。
    real_name = f"{user.last_name}{user.first_name}".strip()
    contact_name = real_name or user.username
    contact_phone = user.mobile or ""

    missing_fields = []
    if not contact_name:
        missing_fields.append("contact_name")
    if not contact_phone:
        missing_fields.append("contact_phone")

    return {
        "user_id": user.id,
        "username": user.username,
        "contact_name": contact_name,
        "contact_phone": contact_phone,
        "mobile": user.mobile,
        "missing_fields": missing_fields,
    }


def serialize_room_type(room_type: RoomType, is_favorite: bool = False) -> dict:
    """功能说明：把房型对象转换为智能体可读的字典。"""
    return {
        "room_type_id": room_type.id,
        "name": room_type.name,
        "price": float(room_type.price),
        "capacity": room_type.capacity,
        "area": room_type.area,
        "bed_type": room_type.bed_type,
        "window": room_type.window,
        "breakfast": room_type.breakfast,
        "description": room_type.description,
        "remaining_stock": room_type.remaining_stock,
        "cover_image": room_type.cover_image,
        "is_favorite": is_favorite,
    }


def serialize_booking(booking: Booking) -> dict:
    """功能说明：把订单对象转换为智能体与前端可读的字典。"""
    return {
        "booking_id": booking.id,
        "room_type_id": booking.room_type_id,
        "room_type_name": booking.room_type.name,
        "room_number": booking.room.room_number if booking.room else "",
        "start_date": booking.start_date,
        "end_date": booking.end_date,
        "stay_days": (booking.end_date - booking.start_date).days,
        "total_price": float(booking.total_price),
        "status": booking.status,
        "status_display": booking.get_status_display(),
        "contact_name": booking.contact_name,
        "contact_phone": booking.contact_phone,
        "payment_method": booking.payment_method,
        "created_at": booking.created_at,
    }
