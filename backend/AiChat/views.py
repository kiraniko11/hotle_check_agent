"""功能说明：AI 对话模块的接口视图。"""

import json
import os
from uuid import uuid4

from django.http import StreamingHttpResponse
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from common.utils import unified_response

from .models import AiChatSession
from .serializers import AiChatRequestSerializer, AiChatSessionSerializer
from .services import get_or_create_chat_session, save_turn_messages, serialize_chat_message

# AI 智能体未配置密钥时返回的友好提示。
LLM_NOT_CONFIGURED_TIP = (
    "AI 智能体尚未配置大模型密钥，请在 backend/.env 中填写 AI_CHAT_API_KEY 后重新发起对话。"
)


def is_llm_configured() -> bool:
    """功能说明：判断是否已配置大模型访问密钥。"""
    return bool(os.getenv("AI_CHAT_API_KEY") or os.getenv("OPENAI_API_KEY"))


def describe_llm_error(exc: Exception) -> str:
    """功能说明：把大模型服务商返回的底层异常翻译成可读的中文提示。"""
    text = str(exc)
    lowered = text.lower()

    # 鉴权失败：OpenAI 兼容服务通常返回 401。
    if "401" in text or "authentication" in lowered or (
            "invalid" in lowered and "key" in lowered):
        return (
            "大模型鉴权失败（401）：API Key 无效或已失效。\n"
            "请确认 backend/.env 中的 AI_CHAT_API_KEY 是目标平台的密钥，"
            "且 AI_CHAT_BASE_URL 与该平台匹配"
            "（DeepSeek 的密钥需配 https://api.deepseek.com）。"
        )
    # 余额不足：DeepSeek 等平台返回 402。
    if "402" in text or "insufficient" in lowered or "balance" in lowered:
        return "大模型账户余额不足（402）：请前往对应平台充值后重试。"
    # 触发限流：返回 429。
    if "429" in text or "rate limit" in lowered:
        return "请求过于频繁（429）：已触发服务商限流，请稍后重试。"
    if "403" in text:
        return "访问被拒绝（403）：密钥权限不足，或当前账号未开通该模型。"
    if "404" in text:
        return "接口或模型不存在（404）：请检查 AI_CHAT_BASE_URL 与 AI_CHAT_MODEL 是否正确。"
    # 网络类异常：连不上服务商。
    if any(token in lowered for token in
           ("connection", "timed out", "timeout", "max retries", "proxy")):
        return "无法连接大模型服务：请检查本机网络或代理，以及 AI_CHAT_BASE_URL 是否可访问。"
    return f"AI 智能体执行失败：{text}"


def build_sse_event(event_name: str, data: object) -> str:
    """功能说明：将事件名称和数据编码为 SSE 文本片段。"""
    payload = json.dumps(data, ensure_ascii=False, default=str)
    return f"event: {event_name}\ndata: {payload}\n\n"


def resolve_session_id(user, raw_session_id: str) -> str:
    """功能说明：校正会话编号，避免不同用户共用同一编号。"""
    if not raw_session_id:
        return uuid4().hex

    # 会话编号已被其他用户占用时重新生成，防止跨用户读取上下文。
    owner = AiChatSession.objects.filter(session_id=raw_session_id).first()
    if owner is not None and owner.user_id != user.id:
        return uuid4().hex
    return raw_session_id


class AiChatAPIView(APIView):
    """功能说明：以同步方式处理当前登录用户与智能体的对话。"""

    permission_classes = (IsAuthenticated,)

    def post(self, request: Request) -> Response:
        """功能说明：接收用户消息并返回智能体的完整回复。"""
        serializer = AiChatRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if not is_llm_configured():
            return unified_response(code=400, msg=LLM_NOT_CONFIGURED_TIP,
                                    data={"reply": LLM_NOT_CONFIGURED_TIP,
                                          "session_id": "", "process_messages": []})

        # 从智能体模块延迟导入，避免未安装 LangGraph 时影响其他接口。
        from AiChat.Agent.graph import run_hotel_agent

        session_id = resolve_session_id(
            request.user, serializer.validated_data.get("session_id", "")
        )
        chat_session = get_or_create_chat_session(
            user=request.user,
            session_id=session_id,
            first_message=serializer.validated_data["message"],
        )

        try:
            result = run_hotel_agent(
                user_id=request.user.id,
                message=serializer.validated_data["message"],
                session_id=session_id,
            )
        except Exception as exc:
            return unified_response(code=500, msg=describe_llm_error(exc))

        # 智能体执行完成后落库，保证刷新页面仍可回看历史对话。
        save_turn_messages(
            session=chat_session,
            user_message=serializer.validated_data["message"],
            reply=result["reply"],
            process_messages=result["process_messages"],
        )
        return unified_response(code=200, msg="对话成功", data=result)


class AiChatStreamAPIView(APIView):
    """功能说明：以 SSE 流式方式处理当前登录用户与智能体的对话。"""

    permission_classes = (IsAuthenticated,)

    def post(self, request: Request) -> StreamingHttpResponse | Response:
        """功能说明：接收用户消息并流式返回 LangGraph 执行过程。"""
        serializer = AiChatRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if not is_llm_configured():
            # 未配置密钥时也必须返回规范的 SSE 流，否则前端按事件解析会收不到任何提示。
            def not_configured_stream():
                """功能说明：以 SSE 形式回传未配置密钥的友好提示。"""
                yield build_sse_event("error", {
                    "reply": LLM_NOT_CONFIGURED_TIP,
                    "session_id": "",
                    "process_messages": [],
                })

            response = StreamingHttpResponse(
                not_configured_stream(), content_type="text/event-stream")
            response["Cache-Control"] = "no-cache"
            response["X-Accel-Buffering"] = "no"
            return response

        # 从智能体模块延迟导入，缩短非 AI 接口的启动耗时。
        from AiChat.Agent.graph import stream_hotel_agent

        # 如果前端没有传会话编号，则生成一个新的会话编号。
        session_id = resolve_session_id(
            request.user, serializer.validated_data.get("session_id", "")
        )
        chat_session = get_or_create_chat_session(
            user=request.user,
            session_id=session_id,
            first_message=serializer.validated_data["message"],
        )
        user_message = serializer.validated_data["message"]

        def event_stream():
            """功能说明：生成 SSE 流式事件文本。"""
            final_data = None
            try:
                for item in stream_hotel_agent(
                    user_id=request.user.id,
                    message=user_message,
                    session_id=session_id,
                ):
                    if item["event"] == "done":
                        final_data = item["data"]
                    yield build_sse_event(item["event"], item["data"])

                # 流式执行完成后，将本轮对话完整写入数据库。
                if final_data is not None:
                    save_turn_messages(
                        session=chat_session,
                        user_message=user_message,
                        reply=final_data["reply"],
                        process_messages=final_data["process_messages"],
                    )
            except Exception as exc:
                yield build_sse_event("error", {
                    "reply": describe_llm_error(exc),
                    "session_id": session_id,
                    "process_messages": [],
                })

        # 返回 SSE 响应，并关闭代理缓存以便前端即时收到数据。
        response = StreamingHttpResponse(event_stream(), content_type="text/event-stream")
        response["Cache-Control"] = "no-cache"
        response["X-Accel-Buffering"] = "no"
        return response


class AiChatSessionListAPIView(APIView):
    """功能说明：列出当前用户的历史 AI 对话会话。"""

    permission_classes = (IsAuthenticated,)

    def get(self, request: Request) -> Response:
        """功能说明：按最近更新时间倒序返回会话列表。"""
        sessions = AiChatSession.objects.filter(user=request.user)
        serializer = AiChatSessionSerializer(sessions, many=True)
        return unified_response(code=200, msg="获取会话列表成功", data=serializer.data)


class AiChatSessionDetailAPIView(APIView):
    """功能说明：查看或删除当前用户的指定 AI 对话会话。"""

    permission_classes = (IsAuthenticated,)

    def get(self, request: Request, session_id: str) -> Response:
        """功能说明：返回指定会话的完整消息记录。"""
        session = AiChatSession.objects.filter(
            user=request.user, session_id=session_id).first()
        if session is None:
            return unified_response(code=404, msg="未找到指定的对话会话",
                                    status_code=status.HTTP_404_NOT_FOUND)

        messages = [
            serialize_chat_message(item)
            for item in session.messages.order_by("created_at", "id")
        ]
        data = AiChatSessionSerializer(session).data
        data["messages"] = messages
        return unified_response(code=200, msg="获取会话详情成功", data=data)

    def delete(self, request: Request, session_id: str) -> Response:
        """功能说明：删除指定会话及其全部消息。"""
        session = AiChatSession.objects.filter(
            user=request.user, session_id=session_id).first()
        if session is None:
            return unified_response(code=404, msg="未找到指定的对话会话",
                                    status_code=status.HTTP_404_NOT_FOUND)

        session.delete()
        return unified_response(code=200, msg="会话已删除")
