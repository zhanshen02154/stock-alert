from typing import Any

from langchain_core.messages import ToolMessage
from src.core.schemas import KBReferenceItem

DEFAULT_REFERENCE_LIMIT = 5
_CONTEXT_MAX_LENGTH = 300
_SOURCE_MAX_LENGTH = 60
_VERSION_MAX_LENGTH = 10


def build_references(
    chunks: list[dict[str, Any]], limit: int = DEFAULT_REFERENCE_LIMIT
) -> list[KBReferenceItem]:
    """
    将知识库工具返回的结构化片段汇总为前端展示的参考资料

    :param chunks: 各次知识库工具调用产生的片段
    :param limit: 最多返回的参考资料数量
    :return: 去重、按得分排序后的参考资料
    """
    unique_chunks: list[dict[str, Any]] = []
    seen: set[str] = set()
    for chunk in chunks:
        source = str(chunk.get("source", "")).strip()
        content = str(chunk.get("content", "")).strip()
        if not source or not content:
            continue
        chunk_id = str(chunk.get("chunk_id", "")).strip() or (
            f"{source}|{chunk.get('chapter_path', '')}|{content[:80]}"
        )
        if chunk_id in seen:
            continue
        seen.add(chunk_id)
        unique_chunks.append(chunk)

    unique_chunks.sort(
        key=lambda chunk: float(chunk.get("score", 0.0) or 0.0), reverse=True
    )

    references: list[KBReferenceItem] = []
    for chunk in unique_chunks[:limit]:
        version = str(chunk.get("version", "")).strip() or "unknown"
        references.append(
            KBReferenceItem(
                source=str(chunk.get("source", ""))[:_SOURCE_MAX_LENGTH],
                version=version[:_VERSION_MAX_LENGTH],
                context=str(chunk.get("content", ""))[:_CONTEXT_MAX_LENGTH],
            )
        )

    return references


def collect_references(
    messages: list[Any], limit: int = DEFAULT_REFERENCE_LIMIT
) -> list[KBReferenceItem]:
    """
    从消息中的工具 artifact 汇总参考资料
    """
    chunks: list[dict[str, Any]] = []
    for message in messages:
        artifact = getattr(message, "artifact", None)
        if isinstance(message, ToolMessage) and isinstance(artifact, dict):
            chunks.extend(artifact.get("chunks", []))

    return build_references(chunks, limit=limit)
