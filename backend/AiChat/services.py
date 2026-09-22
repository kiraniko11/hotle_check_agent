"""功能说明：提供 AI 对话会话和消息的持久化服务。"""

from django.db import transaction
from django.utils import timezone

from AiChat.models import AiChatMessage, AiChatSession


def build_session_title(message: str) -> str:
    """功能说明：根据用户消息生成会话标题。"""
    # 清理换行和多余空白，避免标题展示错位。
    title = " ".join(message.strip().split())

    # 标题过长时截断，保持历史会话列表紧凑。
    return title[:40] or "新的 AI 对话"


def get_or_create_chat_session(user, session_id: str, first_message: str) -> AiChatSession:
    """功能说明：获取或创建当前用户的 AI 对话会话。"""
    # 按用户和会话编号查询，避免访问到其他用户的会话。
    session = AiChatSession.objects.filter(user=user, session_id=session_id).first()
    if session is not None:
        return session

    # 新会话使用首条用户消息生成标题。
    return AiChatSession.objects.create(
        user=user,
        session_id=session_id,
        title=build_session_title(first_message),
    )


def touch_chat_session(session: AiChatSession) -> None:
    """功能说明：刷新 AI 对话会话的最近更新时间。"""
    # 手动更新时间，确保仅保存必要字段。
    session.updated_at = timezone.now()
    session.save(update_fields=["updated_at"])


def save_user_message(session: AiChatSession, content: str) -> AiChatMessage:
    """功能说明：保存用户发送给智能体的消息。"""
    # 创建用户文本消息记录。
    return AiChatMessage.objects.create(
        session=session,
        role=AiChatMessage.Role.USER,
        kind=AiChatMessage.Kind.TEXT,
        content=content,
    )


def save_ai_reply_message(session: AiChatSession, content: str) -> AiChatMessage:
    """功能说明：保存 AI 智能体最终回复消息。"""
    # 创建 AI 回复消息记录。
    return AiChatMessage.objects.create(
        session=session,
        role=AiChatMessage.Role.ASSISTANT,
        kind=AiChatMessage.Kind.REPLY,
        content=content,
    )


def save_process_message(session: AiChatSession, payload: dict) -> AiChatMessage:
    """功能说明：保存 AI 智能体执行过程消息。"""
    # 从过程数据中提取可读摘要，完整结构保存在 JSON 字段中。
    content = payload.get("content") or payload.get("title") or "执行过程"
    return AiChatMessage.objects.create(
        session=session,
        role=AiChatMessage.Role.ASSISTANT,
        kind=AiChatMessage.Kind.PROCESS,
        content=content,
        process_payload=payload,
    )


def should_persist_process_message(payload: dict) -> bool:
    """功能说明：判断过程消息是否需要持久化到数据库。"""
    # 用户消息和最终 AI 回复已有独立记录，不重复保存为过程消息。
    if payload.get("type") == "human":
        return False
    if payload.get("type") == "ai" and not payload.get("has_tool_calls"):
        return False

    # 工具调用、工具结果和 AI 决策过程需要保存。
    return True


def save_turn_messages(
    session: AiChatSession,
    user_message: str,
    reply: str,
    process_messages: list[dict],
) -> None:
    """功能说明：保存单轮用户消息、过程消息和 AI 回复。"""
    # 使用事务保证一轮对话写入的完整性。
    with transaction.atomic():
        # 按对话顺序依次写入用户消息、过程消息和最终回复。
        save_user_message(session, user_message)
        for payload in process_messages:
            if should_persist_process_message(payload):
                save_process_message(session, payload)
        save_ai_reply_message(session, reply)

        # 更新会话最近活跃时间。
        touch_chat_session(session)


def serialize_chat_message(message: AiChatMessage) -> dict:
    """功能说明：将数据库消息转换为前端聊天流结构。"""
    # 过程消息需要保留 process 字段，以复用前端现有过程卡片。
    if message.kind == AiChatMessage.Kind.PROCESS:
        return {
            "id": f"db-message-{message.id}",
            "role": message.role,
            "kind": message.kind,
            "content": message.content,
            "process": message.process_payload,
            "created_at": message.created_at,
        }

    # 文本和回复消息直接返回 content。
    return {
        "id": f"db-message-{message.id}",
        "role": message.role,
        "kind": message.kind,
        "content": message.content,
        "created_at": message.created_at,
    }
