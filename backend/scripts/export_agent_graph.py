"""功能说明：导出酒店预订智能体的 LangGraph 图结构（教学辅助脚本）。

用法（在 backend 目录下执行）：
    python scripts/export_agent_graph.py

脚本会打印官方 Mermaid 图文本，并把渲染后的 PNG 保存到 images/agent_graph.png。
"""

import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django  # noqa: E402

django.setup()

from AiChat.Agent.graph import build_agent  # noqa: E402


class _OfflineStubLLM:
    """功能说明：离线占位模型，仅用于导出图结构，不发起任何真实网络调用。

    这样即便 .env 中尚未填写 AI_CHAT_API_KEY，也能正常导出智能体流程图。
    """

    def bind_tools(self, tools):
        """功能说明：占位实现，返回自身以支持图结构构建。"""
        return self

    def invoke(self, messages):
        """功能说明：占位实现，避免误触发真实调用。"""
        raise RuntimeError("离线占位模型不执行真实调用，请配置 AI_CHAT_API_KEY 后再对话。")


def main() -> None:
    """功能说明：构建智能体并导出图结构。"""
    # user_id 仅用于闭包绑定，构建图结构不会查询数据库。
    agent = build_agent(user_id=1, llm=_OfflineStubLLM())
    graph = agent.get_graph()

    # 方式一：导出 Mermaid 文本。
    print(graph.draw_mermaid())

    # 方式二：直接渲染 PNG 图片（需要联网调用 mermaid.ink 渲染服务）。
    try:
        image_bytes = graph.draw_mermaid_png()
    except Exception as exc:
        print(f"[提示] PNG 渲染失败（通常为网络原因）：{exc}")
        return

    output_path = BASE_DIR / "images" / "agent_graph.png"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(image_bytes)
    print(f"[完成] 图结构已导出到 {output_path}")


if __name__ == "__main__":
    main()
