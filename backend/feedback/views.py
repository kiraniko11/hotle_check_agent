"""功能说明：留言反馈模块的接口视图。"""

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from common.utils import feedback_response

from .models import Feedback
from .serializers import FeedbackSerializer


class FeedbackListCreateView(APIView):
    """功能说明：处理当前用户的问题反馈提交与列表查询。"""

    permission_classes = (IsAuthenticated,)

    def get(self, request: Request) -> Response:
        """功能说明：返回当前用户提交过的问题反馈列表。"""
        queryset = Feedback.objects.filter(user=request.user)
        serializer = FeedbackSerializer(queryset, many=True)
        return feedback_response(code=200, msg="获取反馈列表成功", data=serializer.data)

    def post(self, request: Request) -> Response:
        """功能说明：创建当前用户的问题反馈。"""
        serializer = FeedbackSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # 自动绑定当前登录用户并创建反馈记录。
        feedback = serializer.save(user=request.user)
        return feedback_response(
            code=201,
            msg="反馈提交成功，请等待管理员回复。",
            data=FeedbackSerializer(feedback).data,
            status_code=status.HTTP_201_CREATED,
        )
