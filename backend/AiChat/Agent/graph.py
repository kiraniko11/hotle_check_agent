"""功能说明：编排酒店预订智能体的 LangGraph 状态图。"""

from collections.abc import Iterator

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from .hotel_tools import build_hotel_tools
from .utils.llm_config import get_llm
from .utils.message_utils import (
    build_agent_result,
    format_message_content,
    has_final_ai_message,
)

SYSTEM_PROMPT = """你是酒店预订系统的 AI 助手。
你需要用中文和用户对话，帮助用户查询房型、结合历史预订与收藏分析偏好，并在信息齐全且用户明确确认后创建预订。
你必须遵守：
1. 推荐房型前优先调用 get_user_context 和 search_room_types。
2. 创建订单前必须确认房型编号、入住日期、退房日期；同时优先调用 get_user_profile 获取当前用户资料。
3. 如果 get_user_profile 返回 can_auto_fill_contact=true，不要再询问入住人姓名和联系电话，直接让 create_booking 自动补齐。
4. 只有 get_user_profile 或 create_booking 返回 missing_fields 时，才向用户追问缺失的入住人姓名或联系电话。
5. 如果用户没有明确同意预订，只能推荐或追问，不能调用 create_booking。
6. 工具返回失败时，要向用户解释原因并给出下一步建议。
7. 回复要简洁、自然，并包含关键订单或房型信息。
8. 当用户询问酒店介绍、设施服务、成立历史、发展故事、周边文创景点、游玩美食等非业务数据问题时，必须先调用 search_hotel_knowledge 检索知识库，再根据检索到的资料回答；检索不到就如实说明，不要编造。"""

# 挂载内存检查点，用于保存同一会话的多轮上下文。
MEMORY = InMemorySaver()


def call_model(state: MessagesState, llm_with_tools) -> dict:
    """功能说明：调用绑定业务工具后的 LLM 生成下一步回复或工具调用。"""
    # 构造系统提示和历史消息，保证每轮都遵守预订约束。
    messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]

    # 调用模型节点，返回追加到 LangGraph 消息状态中的 AI 消息。
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}


def build_thread_config(user_id: int, session_id: str) -> dict:
    """功能说明：把会话编号映射为 LangGraph 的线程配置。"""
    # 以用户编号作为命名空间，避免不同用户在内存检查点中复用同一线程。
    return {"configurable": {"thread_id": f"user-{user_id}-{session_id}"}}


def build_agent(user_id: int, llm=None):
    """功能说明：为指定用户构建酒店预订 LangGraph 智能体。

    llm 参数可选：传入自定义对话模型用于离线检查图结构（例如导出流程图），
    不传时按 .env 配置创建真实模型。这样在尚未配置密钥时仍可导出图结构。
    """
    # 构建当前用户可用的业务工具，并绑定到 LLM。
    tools = build_hotel_tools(user_id)
    llm = llm if llm is not None else get_llm()
    llm_with_tools = llm.bind_tools(tools)

    # 初始化消息状态图，显式编排模型节点与工具节点循环。
    graph_builder = StateGraph(MessagesState)
    graph_builder.add_node("agent", lambda state: call_model(state, llm_with_tools))
    graph_builder.add_node("tools", ToolNode(tools))

    # 配置 LangGraph 节点流转：入口进入模型节点，模型可选择调用工具或结束。
    graph_builder.add_edge(START, "agent")
    graph_builder.add_conditional_edges("agent", tools_condition)
    graph_builder.add_edge("tools", "agent")

    # 编译图并挂载内存检查点，支持同一 session_id 下的多轮上下文。
    return graph_builder.compile(checkpointer=MEMORY)


def run_hotel_agent(user_id: int, message: str, session_id: str) -> dict:
    """功能说明：运行酒店预订智能体并返回对话结果。"""
    agent = build_agent(user_id)

    # 将 session_id 映射为 LangGraph thread_id，使同一会话保留历史上下文。
    config = build_thread_config(user_id, session_id)

    result = agent.invoke(
        {"messages": [HumanMessage(content=message)]},
        config=config,
    )

    return build_agent_result(result["messages"], message, session_id)


def stream_hotel_agent(user_id: int, message: str, session_id: str) -> Iterator[dict]:
    """功能说明：以流式事件形式运行酒店预订智能体。"""
    agent = build_agent(user_id)
    config = build_thread_config(user_id, session_id)

    # 先返回开始事件，确保前端立即收到响应，避免长时间等待导致超时。
    yield {"event": "start", "data": {
        "reply": "智能体正在分析你的需求...",
        "session_id": session_id,
        "process_messages": [],
    }}

    final_payload = None
    last_reply = ""
    for stream_mode, payload in agent.stream(
        {"messages": [HumanMessage(content=message)]},
        config=config,
        stream_mode=["messages", "values"],
    ):
        # messages 模式返回 AIMessageChunk，可用于前端逐字显示模型输出。
        if stream_mode == "messages":
            chunk, metadata = payload
            chunk_content = format_message_content(chunk.content)
            if metadata.get("langgraph_node") == "agent" and chunk_content:
                last_reply += chunk_content
                yield {"event": "token", "data": {
                    "token": chunk_content,
                    "reply": last_reply,
                    "session_id": session_id,
                }}

        # values 模式返回当前图状态，可用于展示工具调用和工具结果。
        if stream_mode == "values":
            current_payload = build_agent_result(payload["messages"], message, session_id)
            final_payload = current_payload
            if has_final_ai_message(payload["messages"], message):
                last_reply = current_payload["reply"]
            yield {"event": "message", "data": current_payload}

    # 发送完成事件，前端据此结束 loading 状态。
    yield {"event": "done", "data": final_payload or {
        "reply": last_reply or "智能体已完成本轮处理。",
        "session_id": session_id,
        "process_messages": [],
    }}
