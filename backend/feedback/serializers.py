"""功能说明：留言反馈模块的序列化器。"""

from rest_framework import serializers

from .models import Feedback


class FeedbackSerializer(serializers.ModelSerializer):
    """功能说明：序列化用户留言反馈记录。"""

    username = serializers.CharField(source="user.username", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Feedback
        fields = ("id", "user", "username", "title", "content", "contact", "status",
                  "status_display", "reply_content", "created_at", "replied_at")
        read_only_fields = ("id", "user", "created_at", "replied_at")
