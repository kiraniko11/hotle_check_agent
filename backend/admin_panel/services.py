"""功能说明：管理后台的库存同步等业务服务。"""

from rooms.models import Room, RoomType


def adjust_room_type_stock(room_type_id: int, total_delta: int = 0,
                           remaining_delta: int = 0) -> None:
    """功能说明：按变化量同步指定房型的总库存与剩余库存。"""
    room_type = RoomType.objects.select_for_update().filter(pk=room_type_id).first()
    if room_type is None:
        return

    # 使用非负约束保护库存数据，避免删除或状态切换导致负数。
    room_type.total_stock = max(0, room_type.total_stock + total_delta)
    room_type.remaining_stock = max(0, room_type.remaining_stock + remaining_delta)
    room_type.save(update_fields=["total_stock", "remaining_stock"])


def get_remaining_delta_for_status(status_value: str) -> int:
    """功能说明：根据房间状态计算剩余库存增量基准值。"""
    # 只有空闲房间计入可订剩余库存。
    return 1 if status_value == Room.Status.VACANT else 0
