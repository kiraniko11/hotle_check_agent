"""功能说明：初始化酒店预订系统的演示数据（房型、房间、演示账号）。

用法（在 backend 目录下执行）：
    python scripts/init_data.py
"""

import os
import sys
from pathlib import Path

# 让脚本可以直接以文件方式运行，并指向 Django 项目根目录。
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django  # noqa: E402

django.setup()

from datetime import date, timedelta  # noqa: E402

from django.db import transaction  # noqa: E402

from accounts.models import User  # noqa: E402
from rooms.models import Booking, Favorite, Review, Room, RoomType  # noqa: E402

# 8 种房型的静态配置，与客房数据保持一致的业务口径。
ROOM_TYPES_DATA = [
    {
        "name": "标准大床房",
        "price": 168,
        "capacity": 2,
        "area": 20,
        "bed_type": "1.5米大床",
        "window": True,
        "breakfast": False,
        "description": "房间干净整洁，有空调、无线网络和独立卫浴，热水随用随有，适合日常出行入住。",
        "cover_image": "rooms/photo-1618773928121-c32242e63f39.avif",
    },
    {
        "name": "标准双床房",
        "price": 188,
        "capacity": 2,
        "area": 24,
        "bed_type": "1.2米单人床 x 2",
        "window": True,
        "breakfast": False,
        "description": "两张单人床，适合朋友或同事一起住，带书桌和衣柜，晚上安静不吵。",
        "cover_image": "rooms/photo-1566665797739-1674de7a421a.avif",
    },
    {
        "name": "舒适大床房",
        "price": 218,
        "capacity": 2,
        "area": 28,
        "bed_type": "1.8米大床",
        "window": True,
        "breakfast": True,
        "description": "房间比标准间宽敞一些，采光好，含简单早餐，性价比不错。",
        "cover_image": "rooms/photo-1590490360182-c33d57733427.avif",
    },
    {
        "name": "家庭房",
        "price": 258,
        "capacity": 3,
        "area": 32,
        "bed_type": "1.8米大床 + 1.2米单床",
        "window": True,
        "breakfast": False,
        "description": "适合一家三口住，空间够大，楼下有便利店和公交站，出行方便。",
        "cover_image": "rooms/photo-1582719508461-905c673771fd.avif",
    },
    {
        "name": "商务双床房",
        "price": 268,
        "capacity": 2,
        "area": 30,
        "bed_type": "1.2米单人床 x 2",
        "window": True,
        "breakfast": True,
        "description": "带小办公桌和免费无线网络，含早餐，出差住着比较方便。",
        "cover_image": "rooms/photo-1611892440504-42a792e24d32.avif",
    },
    {
        "name": "经济单人间",
        "price": 98,
        "capacity": 1,
        "area": 15,
        "bed_type": "1.2米单床",
        "window": False,
        "breakfast": False,
        "description": "面积不大但该有的都有，热水、空调、无线网齐全，适合一个人短期住宿。",
        "cover_image": "rooms/photo-1631049307264-da0ec9d70304.avif",
    },
    {
        "name": "大床房（带窗）",
        "price": 238,
        "capacity": 2,
        "area": 26,
        "bed_type": "1.8米大床",
        "window": True,
        "breakfast": False,
        "description": "朝南带窗，白天光线好，床品干净，睡得踏实。",
        "cover_image": "rooms/photo-1631049552240-59c37f38802b.avif",
    },
    {
        "name": "家庭套房",
        "price": 358,
        "capacity": 4,
        "area": 45,
        "bed_type": "两间房：1.8米大床 + 1.5米床",
        "window": True,
        "breakfast": True,
        "description": "两间独立的房间，适合一家人或几个朋友一起住，含简单早餐。",
        "cover_image": "rooms/photo-1631049421450-348ccd7f8949.avif",
    },
]

# 每种房型对应的物理房间，共 35 间客房。
ROOMS_DATA = {
    "标准大床房": [
        {"room_number": "201", "status": Room.Status.OCCUPIED, "floor": 2},
        {"room_number": "202", "status": Room.Status.VACANT, "floor": 2},
        {"room_number": "203", "status": Room.Status.OCCUPIED, "floor": 2},
        {"room_number": "204", "status": Room.Status.VACANT, "floor": 2},
        {"room_number": "205", "status": Room.Status.CLEANING, "floor": 2},
        {"room_number": "206", "status": Room.Status.VACANT, "floor": 2},
    ],
    "标准双床房": [
        {"room_number": "211", "status": Room.Status.VACANT, "floor": 2},
        {"room_number": "212", "status": Room.Status.VACANT, "floor": 2},
        {"room_number": "213", "status": Room.Status.OCCUPIED, "floor": 2},
        {"room_number": "214", "status": Room.Status.VACANT, "floor": 2},
        {"room_number": "215", "status": Room.Status.VACANT, "floor": 2},
    ],
    "舒适大床房": [
        {"room_number": "301", "status": Room.Status.VACANT, "floor": 3},
        {"room_number": "302", "status": Room.Status.VACANT, "floor": 3},
        {"room_number": "303", "status": Room.Status.OCCUPIED, "floor": 3},
        {"room_number": "304", "status": Room.Status.VACANT, "floor": 3},
        {"room_number": "305", "status": Room.Status.MAINTENANCE, "floor": 3},
    ],
    "家庭房": [
        {"room_number": "401", "status": Room.Status.VACANT, "floor": 4},
        {"room_number": "402", "status": Room.Status.VACANT, "floor": 4},
        {"room_number": "403", "status": Room.Status.VACANT, "floor": 4},
        {"room_number": "404", "status": Room.Status.CLEANING, "floor": 4},
    ],
    "商务双床房": [
        {"room_number": "501", "status": Room.Status.VACANT, "floor": 5},
        {"room_number": "502", "status": Room.Status.VACANT, "floor": 5},
        {"room_number": "503", "status": Room.Status.OCCUPIED, "floor": 5},
        {"room_number": "504", "status": Room.Status.VACANT, "floor": 5},
    ],
    "经济单人间": [
        {"room_number": "101", "status": Room.Status.VACANT, "floor": 1},
        {"room_number": "102", "status": Room.Status.VACANT, "floor": 1},
        {"room_number": "103", "status": Room.Status.VACANT, "floor": 1},
        {"room_number": "104", "status": Room.Status.OCCUPIED, "floor": 1},
        {"room_number": "105", "status": Room.Status.VACANT, "floor": 1},
        {"room_number": "106", "status": Room.Status.CLEANING, "floor": 1},
    ],
    "大床房（带窗）": [
        {"room_number": "601", "status": Room.Status.VACANT, "floor": 6},
        {"room_number": "602", "status": Room.Status.VACANT, "floor": 6},
        {"room_number": "603", "status": Room.Status.OCCUPIED, "floor": 6},
    ],
    "家庭套房": [
        {"room_number": "701", "status": Room.Status.VACANT, "floor": 7},
        {"room_number": "702", "status": Room.Status.VACANT, "floor": 7},
    ],
}


def ensure_admin_account() -> User:
    """功能说明：创建或更新后台超级管理员账号。"""
    admin, created = User.objects.get_or_create(
        username="admin",
        defaults={
            "mobile": "13800138000",
            "role": User.Role.ADMIN,
            "is_staff": True,
            "is_superuser": True,
            "last_name": "管",
            "first_name": "理员",
        },
    )
    admin.role = User.Role.ADMIN
    admin.is_staff = True
    admin.is_superuser = True
    admin.set_password("admin123456")
    admin.save()
    print(f"[账号] 管理员 admin 已{'创建' if created else '更新'}，密码 admin123456")
    return admin


def ensure_demo_user() -> User:
    """功能说明：创建或更新用于演示的普通用户账号。"""
    user, created = User.objects.get_or_create(
        username="guest",
        defaults={"mobile": "13900139000", "role": User.Role.USER},
    )
    user.role = User.Role.USER
    user.last_name = user.last_name or "王"
    user.first_name = user.first_name or "小明"
    user.email = user.email or "guest@hotel.local"
    user.set_password("guest123456")
    user.save()
    print(f"[账号] 演示用户 guest 已{'创建' if created else '更新'}，密码 guest123456")
    return user


def reset_room_data() -> None:
    """功能说明：清空既有业务与客房数据，避免演示数据重复。

    注意：该函数会清除订单、评价、收藏、房间与房型数据，仅用于演示环境初始化。
    必须先清理订单等引用数据，否则房型被 PROTECT 外键保护无法删除。
    """
    Booking.objects.all().delete()
    Review.objects.all().delete()
    Favorite.objects.all().delete()
    Room.objects.all().delete()
    RoomType.objects.all().delete()
    print("[数据] 已清空旧的订单、评价、收藏、房型与房间数据")


def create_room_types_and_rooms() -> dict[str, RoomType]:
    """功能说明：批量创建房型与物理房间，并反算库存。"""
    created_types = {}
    for type_item in ROOM_TYPES_DATA:
        rt = RoomType.objects.create(
            name=type_item["name"],
            price=type_item["price"],
            capacity=type_item["capacity"],
            area=type_item["area"],
            bed_type=type_item["bed_type"],
            window=type_item["window"],
            breakfast=type_item["breakfast"],
            description=type_item["description"],
            cover_image=type_item["cover_image"],
            total_stock=0,
            remaining_stock=0,
        )
        created_types[rt.name] = rt

    # 遍历写入具体客房实体。
    for name, rt in created_types.items():
        for room_item in ROOMS_DATA.get(name, []):
            Room.objects.create(
                room_number=room_item["room_number"],
                room_type=rt,
                status=room_item["status"],
                floor=room_item["floor"],
            )

        # 动态统计并重新保存各房型的总库存与空闲可用库存。
        total_count = rt.rooms.count()
        vacant_count = rt.rooms.filter(status=Room.Status.VACANT).count()
        rt.total_stock = total_count
        rt.remaining_stock = vacant_count
        rt.save(update_fields=["total_stock", "remaining_stock"])

    print(f"[数据] 已创建 {len(created_types)} 种房型、{Room.objects.count()} 间客房")
    return created_types


def create_demo_business_data(user: User, room_types: dict[str, RoomType]) -> None:
    """功能说明：为演示账号生成少量订单、收藏与评价数据。"""
    if Booking.objects.filter(user=user).exists():
        print("[数据] 演示账号已存在业务数据，跳过订单与评价生成")
        return

    demo_orders = [
        ("舒适大床房", 12, 14, Booking.Status.COMPLETED),
        ("大床房（带窗）", 20, 22, Booking.Status.BOOKED),
    ]

    for name, start_offset, end_offset, order_status in demo_orders:
        room_type = room_types.get(name)
        if room_type is None:
            continue

        room = Room.objects.filter(room_type=room_type,
                                   status=Room.Status.VACANT).first()
        if room is None:
            continue

        start_date = date.today() + timedelta(days=start_offset)
        end_date = date.today() + timedelta(days=end_offset)

        with transaction.atomic():
            room.status = Room.Status.OCCUPIED
            room.save(update_fields=["status"])
            room_type.remaining_stock = max(0, room_type.remaining_stock - 1)
            room_type.save(update_fields=["remaining_stock"])

            Booking.objects.create(
                user=user,
                room_type=room_type,
                room=room,
                start_date=start_date,
                end_date=end_date,
                total_price=room_type.price * (end_date - start_date).days,
                contact_name="王小明",
                contact_phone="13900139000",
                payment_method="hang_charge",
                status=order_status,
            )

    # 收藏两间房型，方便体验收藏列表与智能体推荐排序。
    for name in ("标准双床房", "家庭套房"):
        room_type = room_types.get(name)
        if room_type is not None:
            Favorite.objects.get_or_create(user=user, room_type=room_type)

    # 为已完成订单补一条真实评价。
    completed_type = room_types.get("舒适大床房")
    if completed_type is not None:
        Review.objects.get_or_create(
            user=user,
            room_type=completed_type,
            defaults={
                "rating": 5,
                "content": "房间宽敞采光好，床垫软硬合适，早餐虽然简单但管饱，出差住着挺舒服。",
            },
        )

    print("[数据] 已生成演示订单、收藏与评价数据")


def main() -> None:
    """功能说明：执行演示数据初始化主流程。"""
    print("=" * 56)
    print("酒店预订系统演示数据初始化")
    print("=" * 56)

    ensure_admin_account()
    demo_user = ensure_demo_user()
    reset_room_data()
    room_types = create_room_types_and_rooms()
    create_demo_business_data(demo_user, room_types)

    print("-" * 56)
    print("初始化完成，可使用以下账号登录：")
    print("  管理端  http://localhost:5173/admin/login   admin / admin123456")
    print("  用户端  http://localhost:5173/login         guest / guest123456")
    print("=" * 56)


if __name__ == "__main__":
    main()
