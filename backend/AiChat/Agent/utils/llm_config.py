"""功能说明：根据环境变量创建兼容 OpenAI 协议的对话模型。"""

import os

from langchain_openai import ChatOpenAI


def get_llm() -> ChatOpenAI:
    """功能说明：根据 .env 环境变量创建 ChatOpenAI 对话模型。"""
    model_name = os.getenv("AI_CHAT_MODEL", "deepseek-chat")
    api_key = os.getenv("AI_CHAT_API_KEY") or os.getenv("OPENAI_API_KEY") or ""

    # 未配置密钥时直接给出明确提示，避免抛出难以理解的 OpenAI 底层异常。
    if not api_key:
        raise ValueError(
            "未配置大模型密钥，请在 backend/.env 中填写 AI_CHAT_API_KEY（或 OPENAI_API_KEY）。"
        )

    try:
        temperature = float(os.getenv("AI_CHAT_TEMPERATURE", "0.2"))
    except ValueError:
        temperature = 0.2

    base_url = os.getenv("AI_CHAT_BASE_URL") or None

    return ChatOpenAI(
        model=model_name,
        temperature=temperature,
        base_url=base_url,
        api_key=api_key,
        streaming=True,
    )
