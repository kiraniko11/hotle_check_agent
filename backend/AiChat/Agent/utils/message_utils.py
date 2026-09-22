"""功能说明：处理 LangGraph 消息状态与前端展示结构之间的转换。"""

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage


def format_message_content(content) -> str:
    """功能说明：把模型返回的多段内容统一转换为纯文本。"""
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                # 兼容 OpenAI 多模态内容块结构。
                parts.append(str(item.get("text") or item.get("content") or ""))
        return "".join(parts)
    return str(content)


def get_current_turn_messages(messages: list, user_message: str) -> list:
    """功能说明：从完整对话历史中截取本轮产生的消息。"""
    target_index = None
    # 从后往前定位本轮用户消息，避免多轮会话时前端重复展示历史过程。
    for index in range(len(messages) - 1, -1, -1):
        item = messages[index]
        if isinstance(item, HumanMessage) and format_message_content(item.content) == user_message:
            target_index = index
            break

    if target_index is None:
        return list(messages)
    return list(messages[target_index:])


def extract_last_ai_message(messages: list) -> str:
    """功能说明：提取最后一条不带工具调用的 AI 文本回复。"""
    for item in reversed(messages):
        if isinstance(item, AIMessage) and not getattr(item, "tool_calls", None):
            text = format_message_content(item.content)
            if text:
                return text
    return ""


def has_final_ai_message(messages: list, user_message: str) -> bool:
    """功能说明：判断本轮对话是否已经产出最终回复。"""
    turn_messages = get_current_turn_messages(messages, user_message)
    if not turn_messages:
        return False

    last_message = turn_messages[-1]
    return isinstance(last_message, AIMessage) and not getattr(last_message, "tool_calls", None)


def serialize_tool_call(tool_call: dict) -> dict:
    """功能说明：整理单个工具调用的展示信息。"""
    return {
        "name": tool_call.get("name", ""),
        "args": tool_call.get("args", {}),
        "id": tool_call.get("id", ""),
    }


def serialize_agent_message(message) -> dict | None:
    """功能说明：把单条 LangChain 消息转换为前端可渲染的过程结构。"""
    if isinstance(message, HumanMessage):
        return {
            "type": "human",
            "title": "用户提问",
            "content": format_message_content(message.content),
        }

    if isinstance(message, AIMessage):
        tool_calls = [serialize_tool_call(item) for item in (message.tool_calls or [])]
        if tool_calls:
            names = "、".join(item["name"] for item in tool_calls if item["name"])
            return {
                "type": "ai",
                "title": "智能体决策",
                "content": f"决定调用工具：{names}" if names else "准备调用业务工具",
                "has_tool_calls": True,
                "tool_calls": tool_calls,
            }

        content = format_message_content(message.content)
        if not content:
            return None
        return {
            "type": "ai",
            "title": "智能体回复",
            "content": content,
            "has_tool_calls": False,
        }

    if isinstance(message, ToolMessage):
        content = format_message_content(message.content)
        tool_name = getattr(message, "name", "") or "业务工具"
        # 工具层统一返回 JSON 字符串，这里提取 success 字段判断执行结果。
        success = '"success": true' in content.replace(" ", "").lower() or \
            '"success":true' in content.replace(" ", "").lower()
        return {
            "type": "tool",
            "title": f"工具调用结果 · {tool_name}",
            "content": content,
            "tool_name": tool_name,
            "success": success,
        }

    return None


def serialize_agent_messages(messages: list) -> list[dict]:
    """功能说明：批量转换消息列表，并过滤空节点。"""
    result = []
    for message in messages:
        payload = serialize_agent_message(message)
        if payload is not None:
            result.append(payload)
    return result


def build_agent_result(messages: list, user_message: str, session_id: str) -> dict:
    """功能说明：组装单轮对话的完整返回结构。"""
    turn_messages = get_current_turn_messages(messages, user_message)
    reply = extract_last_ai_message(turn_messages) or "智能体已完成本轮处理。"

    return {
        "reply": reply,
        "session_id": session_id,
        "process_messages": serialize_agent_messages(turn_messages),
    }
