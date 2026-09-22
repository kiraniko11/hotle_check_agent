"""功能说明：酒店知识库的构建与检索（RAG 向量检索模块）。

流程：读取 knowledge/ 目录下的 Markdown 文档 → 按标题和段落切块 →
本地嵌入模型（bge-small-zh）向量化 → 存入 Chroma 持久化向量库 →
智能体检索工具按相似度取回最相关的资料片段。
"""

import os
from pathlib import Path

# 国内网络下默认使用 HuggingFace 镜像站下载嵌入模型。
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

BASE_DIR = Path(__file__).resolve().parent.parent
KNOWLEDGE_DIR = BASE_DIR / "knowledge"
VECTOR_DIR = BASE_DIR / "vector_store"

# 检索参数：每块最大字符数、相邻块重叠字符数、默认返回条数。
CHUNK_SIZE = 400
CHUNK_OVERLAP = 80
DEFAULT_TOP_K = 4

_embedding_model = None
_collection = None


def _get_embedding_model():
    """功能说明：懒加载本地中文嵌入模型，避免 Django 启动时就占用内存。"""
    global _embedding_model
    if _embedding_model is None:
        from sentence_transformers import SentenceTransformer

        model_name = os.getenv("KNOWLEDGE_EMBEDDING_MODEL", "BAAI/bge-small-zh-v1.5")
        _embedding_model = SentenceTransformer(model_name)
    return _embedding_model


def _get_collection():
    """功能说明：获取或创建 Chroma 持久化集合（余弦相似度）。"""
    global _collection
    if _collection is None:
        import chromadb

        client = chromadb.PersistentClient(path=str(VECTOR_DIR))
        _collection = client.get_or_create_collection(
            name="hotel_knowledge",
            metadata={"hnsw:space": "cosine"},
        )
    return _collection


def _split_long_text(text: str) -> list[str]:
    """功能说明：把超长文本按固定窗口切分，窗口之间保留一定重叠。"""
    if len(text) <= CHUNK_SIZE:
        return [text]

    chunks = []
    step = CHUNK_SIZE - CHUNK_OVERLAP
    for start in range(0, len(text), step):
        piece = text[start:start + CHUNK_SIZE].strip()
        if len(piece) >= 30:
            chunks.append(piece)
        if start + CHUNK_SIZE >= len(text):
            break
    return chunks


def load_document_chunks() -> list[dict]:
    """功能说明：读取 knowledge/ 下全部 Markdown 文档并切块。

    切块策略：先按二级标题（##）拆出小节，小节超过 CHUNK_SIZE 时再滑窗细分，
    保证每个块语义完整且携带来源文档信息。
    """
    chunks: list[dict] = []
    for doc_path in sorted(KNOWLEDGE_DIR.glob("*.md")):
        raw_lines = doc_path.read_text(encoding="utf-8").splitlines()
        doc_title = next(
            (line.lstrip("# ").strip() for line in raw_lines if line.startswith("# ")),
            doc_path.stem,
        )

        # 按二级标题切节，标题行归入本节首块，方便向量检索命中标题。
        sections: list[list[str]] = []
        for line in raw_lines:
            if line.startswith("## "):
                sections.append([line])
            elif not sections:
                continue
            else:
                sections[-1].append(line)

        for section_lines in sections:
            section_text = "\n".join(section_lines).strip()
            if len(section_text) < 30:
                continue
            for piece in _split_long_text(section_text):
                chunks.append({
                    "text": piece,
                    "source": doc_path.name,
                    "title": doc_title,
                })
    return chunks


def build_knowledge_base(force_rebuild: bool = False) -> int:
    """功能说明：把知识文档向量化写入 Chroma，返回写入的块数量。

    force_rebuild=True 时先清空旧数据再全量重建（文档更新后需重建）。
    """
    chunks = load_document_chunks()
    if not chunks:
        raise FileNotFoundError(
            f"知识目录 {KNOWLEDGE_DIR} 下没有找到 Markdown 文档。"
        )

    collection = _get_collection()
    if collection.count() > 0:
        if not force_rebuild:
            return collection.count()
        # 全量重建：先删除集合再重新创建，避免旧向量残留。
        collection.client.delete_collection("hotel_knowledge")
        global _collection
        _collection = None
        collection = _get_collection()

    model = _get_embedding_model()
    texts = [chunk["text"] for chunk in chunks]
    embeddings = model.encode(texts, normalize_embeddings=True).tolist()

    collection.add(
        ids=[f"{chunk['source']}#{index}" for index, chunk in enumerate(chunks)],
        documents=texts,
        embeddings=embeddings,
        metadatas=[
            {"source": chunk["source"], "title": chunk["title"]}
            for chunk in chunks
        ],
    )
    return collection.count()


def search_knowledge(query: str, top_k: int = DEFAULT_TOP_K) -> str:
    """功能说明：按语义相似度检索酒店知识库，返回格式化的资料片段。"""
    query = (query or "").strip()
    if not query:
        return "检索失败：检索词不能为空。"

    collection = _get_collection()
    if collection.count() == 0:
        # 首次调用时自动构建，保证未手动执行构建脚本也能检索。
        build_knowledge_base()

    model = _get_embedding_model()
    query_vector = model.encode([query], normalize_embeddings=True).tolist()

    actual_k = min(top_k, collection.count())
    result = collection.query(
        query_embeddings=query_vector,
        n_results=actual_k,
    )

    documents = result.get("documents", [[]])[0]
    metadatas = result.get("metadatas", [[]])[0]
    distances = result.get("distances", [[]])[0]

    if not documents:
        return "知识库为空，未检索到相关资料。"

    lines = [f"共检索到 {len(documents)} 条相关资料：\n"]
    for index, (doc, meta, dist) in enumerate(zip(documents, metadatas, distances), start=1):
        similarity = round(1 - dist, 3)
        source = meta.get("source", "未知来源") if meta else "未知来源"
        lines.append(f"【资料{index}】来源：{source}（相似度 {similarity}）")
        lines.append(doc.strip())
        lines.append("")
    return "\n".join(lines)
