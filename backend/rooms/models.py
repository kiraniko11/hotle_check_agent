"""功能说明：定义客房相关的房型、房间、订单、评价与收藏模型。"""

from django.conf import settings
from django.db import models


class RoomType(models.Model):
    """功能说明：保存房型的基础资料、设施标签与库存信息。"""

    name = models.CharField("房型名称", max_length=100, unique=True)
    price = models.DecimalField("每晚价格", max_digits=10, decimal_places=2)
    capacity = models.PositiveIntegerField("可住人数")
    area = models.PositiveIntegerField("面积（平方米）")
    bed_type = models.CharField("床型说明", max_length=100)
    window = models.BooleanField("是否有窗", default=True)
    breakfast = models.BooleanField("是否含早餐", default=False)
    description = models.TextField("房型描述")
    cover_image = models.CharField("封面图片", max_length=255, blank=True, default="")
    total_stock = models.PositiveIntegerField("总库存", default=0)
    remaining_stock = models.PositiveIntegerField("剩余库存", default=0)

    class Meta:
        db_table = "room_type"
        db_table_comment = "房间类型"
        verbose_name = "房型"
        verbose_name_plural = "房型"
        ordering = ("price", "id")

    def __str__(self) -> str:
        return self.name


class Room(models.Model):
    """功能说明：保存具体物理客房实体及其占用状态。"""

    class Status(models.TextChoices):
        """功能说明：定义客房的物理占用与清洁状态。"""
        VACANT = "vacant", "空闲"
        OCCUPIED = "occupied", "已入住"
        CLEANING = "cleaning", "清洁中"
        MAINTENANCE = "maintenance", "维修中"

    room_number = models.CharField("房间号", max_length=20, unique=True)
    room_type = models.ForeignKey(RoomType, on_delete=models.CASCADE,
                                  related_name="rooms", verbose_name="所属房型")
    status = models.CharField("房间状态", max_length=20, choices=Status.choices,
                              default=Status.VACANT)
    floor = models.IntegerField("楼层", default=1)

    class Meta:
        db_table = "room"
        db_table_comment = "房间信息"
        verbose_name = "房间"
        verbose_name_plural = "房间"
        ordering = ("room_number",)

    def __str__(self) -> str:
        return f"{self.room_number}（{self.room_type.name}）"


class Booking(models.Model):
    """功能说明：保存宾客的客房预订订单。"""

    class Status(models.TextChoices):
        """功能说明：定义订单的业务状态。"""
        BOOKED = "booked", "已预订"
        CHECKED_IN = "checked_in", "已入住"
        COMPLETED = "completed", "已完成"
        CANCELLED = "cancelled", "已取消"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name="bookings", verbose_name="预订用户")
    room_type = models.ForeignKey(RoomType, on_delete=models.PROTECT,
                                  related_name="bookings", verbose_name="房型")
    room = models.ForeignKey(Room, on_delete=models.SET_NULL, null=True, blank=True,
                             related_name="bookings", verbose_name="分配房间")
    start_date = models.DateField("入住日期")
    end_date = models.DateField("退房日期")
    total_price = models.DecimalField("订单总价", max_digits=10, decimal_places=2, default=0)
    contact_name = models.CharField("入住人姓名", max_length=50, blank=True, default="")
    contact_phone = models.CharField("联系电话", max_length=11, blank=True, default="")
    id_card = models.CharField("身份证号", max_length=18, blank=True, default="")
    payment_method = models.CharField("支付方式", max_length=30, default="hang_charge")
    status = models.CharField("订单状态", max_length=20, choices=Status.choices,
                              default=Status.BOOKED)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        db_table = "booking"
        db_table_comment = "预订订单"
        verbose_name = "预订订单"
        verbose_name_plural = "预订订单"
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"订单{self.id} - {self.room_type.name}"


class Review(models.Model):
    """功能说明：保存宾客对房型的评分与文字评价。"""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name="reviews", verbose_name="评价用户")
    room_type = models.ForeignKey(RoomType, on_delete=models.CASCADE,
                                  related_name="reviews", verbose_name="房型")
    rating = models.PositiveSmallIntegerField("评分", default=5)
    content = models.TextField("评价内容")
    created_at = models.DateTimeField("评价时间", auto_now_add=True)

    class Meta:
        db_table = "review"
        db_table_comment = "房型评价"
        verbose_name = "房型评价"
        verbose_name_plural = "房型评价"
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"{self.user.username} - {self.room_type.name} - {self.rating}星"


class Favorite(models.Model):
    """功能说明：保存用户对房型的收藏记录。"""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name="favorites", verbose_name="收藏用户")
    room_type = models.ForeignKey(RoomType, on_delete=models.CASCADE,
                                  related_name="favorites", verbose_name="收藏房型")
    created_at = models.DateTimeField("收藏时间", auto_now_add=True)

    class Meta:
        db_table = "favorite"
        db_table_comment = "房型收藏"
        verbose_name = "房型收藏"
        verbose_name_plural = "房型收藏"
        ordering = ("-created_at",)
        # 同一用户对同一房型只能保留一条收藏记录。
        unique_together = ("user", "room_type")

    def __str__(self) -> str:
        return f"{self.user.username} 收藏 {self.room_type.name}"
