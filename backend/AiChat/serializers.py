"""功能说明：AI 对话模块的序列化器。"""

from rest_framework import serializers

from .models import AiChatMessage, AiChatSession
from .services import serialize_chat_message


class AiChatRequestSerializer(serializers.Serializer):
    """功能说明：校验前端发起 AI 对话时的入参。"""

    message = serializers.CharField(max_length=2000, label="用户消息")
    session_id = serializers.CharField(max_length=100, required=False, allow_blank=True,
                                       label="会话编号")


class AiChatMessageSerializer(serializers.ModelSerializer):
    """功能说明：把数据库消息序列化为前端聊天流结构。"""

    process = serializers.JSONField(source="process_payload", read_only=True)

    class Meta:
        model = AiChatMessage
        fields = ("id", "role", "kind", "content", "process", "created_at")

    def to_representation(self, instance):
        """功能说明：复用持久化服务的序列化结果，保证前后端结构一致。"""
        return serialize_chat_message(instance)


class AiChatSessionSerializer(serializers.ModelSerializer):
    """功能说明：序列化 AI 对话会话及其概览信息。"""

    message_count = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = AiChatSession
        fields = ("id", "session_id", "title", "message_count", "last_message",
                  "created_at", "updated_at")

    def get_message_count(self, obj) -> int:
        """功能说明：统计会话中的消息总数。"""
        return obj.messages.count()

    def get_last_message(self, obj) -> str:
        """功能说明：取会话中最后一条可展示的文本内容。"""
        last = obj.messages.exclude(kind=AiChatMessage.Kind.PROCESS).order_by("-id").first()
        return last.content[:60] if last else ""
