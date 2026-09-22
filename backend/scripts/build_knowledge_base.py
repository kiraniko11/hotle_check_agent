"""功能说明：构建酒店知识向量库（RAG）。

用法（在 backend 目录下执行）：
    .\\.venv\\Scripts\\python.exe scripts\\build_knowledge_base.py

脚本会读取 AiChat/Agent/knowledge/ 下的全部 Markdown 文档，
切块并向量化后存入 AiChat/Agent/vector_store/ 的 Chroma 持久化库。
文档内容更新后重新执行本脚本即可（脚本默认全量重建）。
"""

import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django  # noqa: E402

django.setup()

from AiChat.Agent.utils.knowledge import (  # noqa: E402
    KNOWLEDGE_DIR,
    build_knowledge_base,
    load_document_chunks,
    search_knowledge,
)


def main() -> None:
    chunks = load_document_chunks()
    print(f"读取知识文档目录：{KNOWLEDGE_DIR}")
    print(f"共切分出 {len(chunks)} 个知识块：")
    source_count: dict[str, int] = {}
    for chunk in chunks:
        source_count[chunk["source"]] = source_count.get(chunk["source"], 0) + 1
    for source, count in source_count.items():
        print(f"  - {source}: {count} 块")

    total = build_knowledge_base(force_rebuild=True)
    print(f"向量库构建完成，共写入 {total} 个向量。")

    # 构建后跑一次示例检索，验证向量库可用。
    demo_query = "酒店是什么时候成立的"
    print(f"\n示例检索：{demo_query}")
    print("-" * 40)
    print(search_knowledge(demo_query, top_k=2))


if __name__ == "__main__":
    main()
