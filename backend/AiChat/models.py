"""功能说明：定义 AI 对话的会话与消息模型。"""

from django.conf import settings
from django.db import models


class AiChatSession(models.Model):
    """功能说明：保存用户与 AI 智能体的对话会话。"""

    id = models.BigAutoField("编号", primary_key=True, db_comment="AI 对话会话唯一编号")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name="ai_chat_sessions", verbose_name="用户",
                             db_comment="发起 AI 对话的系统用户")
    session_id = models.CharField("会话编号", max_length=100, unique=True,
                                  db_comment="前端与 LangGraph 共享的会话编号")
    title = models.CharField("会话标题", max_length=120,
                             db_comment="根据用户首条消息生成的会话标题")
    created_at = models.DateTimeField("创建时间", auto_now_add=True, db_comment="会话创建时间")
    updated_at = models.DateTimeField("更新时间", auto_now=True, db_comment="会话最近更新时间")

    class Meta:
        db_table = "ai_chat_session"
        db_table_comment = "AI 对话会话"
        verbose_name = "AI 对话会话"
        verbose_name_plural = "AI 对话会话"
        ordering = ("-updated_at",)

    def __str__(self) -> str:
        return self.title


class AiChatMessage(models.Model):
    """功能说明：保存 AI 对话中的用户消息、AI 回复和工具过程。"""

    class Role(models.TextChoices):
        """功能说明：定义消息的发送方角色。"""
        USER = "user", "用户"
        ASSISTANT = "assistant", "AI"

    class Kind(models.TextChoices):
        """功能说明：定义消息在对话流中的类型。"""
        TEXT = "text", "用户文本"
        REPLY = "reply", "AI 回复"
        PROCESS = "process", "执行过程"

    id = models.BigAutoField("编号", primary_key=True, db_comment="AI 对话消息唯一编号")
    session = models.ForeignKey(AiChatSession, on_delete=models.CASCADE,
                                related_name="messages", verbose_name="所属会话",
                                db_comment="消息所属的 AI 对话会话")
    role = models.CharField("消息角色", max_length=20, choices=Role.choices,
                            db_comment="消息发送方角色")
    kind = models.CharField("消息类型", max_length=20, choices=Kind.choices,
                            db_comment="消息在对话流中的类型")
    content = models.TextField("消息内容", blank=True, default="",
                               db_comment="用户输入、AI 回复或过程摘要内容")
    process_payload = models.JSONField("过程数据", default=dict, blank=True,
                                       db_comment="工具调用、工具结果等过程消息的结构化数据")
    created_at = models.DateTimeField("创建时间", auto_now_add=True, db_comment="消息创建时间")

    class Meta:
        db_table = "ai_chat_message"
        db_table_comment = "AI 对话消息"
        verbose_name = "AI 对话消息"
        verbose_name_plural = "AI 对话消息"
        ordering = ("created_at", "id")

    def __str__(self) -> str:
        return f"{self.get_role_display()} - {self.content[:30]}"
