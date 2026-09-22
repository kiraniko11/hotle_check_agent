"""功能说明：定义用户留言反馈模型。"""

from django.conf import settings
from django.db import models


class Feedback(models.Model):
    """功能说明：保存用户提交的问题反馈与管理员回复。"""

    class Status(models.TextChoices):
        """功能说明：定义问题反馈的处理状态。"""
        PENDING = "pending", "待回复"
        REPLIED = "replied", "已回复"
        CLOSED = "closed", "已关闭"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name="feedbacks", verbose_name="反馈用户")
    title = models.CharField("反馈标题", max_length=100)
    content = models.TextField("反馈内容")
    contact = models.CharField("联系方式", max_length=100, blank=True, default="")
    status = models.CharField("处理状态", max_length=20, choices=Status.choices,
                              default=Status.PENDING)
    reply_content = models.TextField("回复内容", blank=True, default="")
    created_at = models.DateTimeField("提交时间", auto_now_add=True)
    replied_at = models.DateTimeField("回复时间", null=True, blank=True)

    class Meta:
        db_table = "feedback"
        db_table_comment = "用户留言反馈"
        verbose_name = "用户留言反馈"
        verbose_name_plural = "用户留言反馈"
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return self.title
