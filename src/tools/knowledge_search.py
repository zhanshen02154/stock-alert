from langchain_core.tools import tool

from src.knowledge.retriever import BaseKnowledgeRetriever
from src.knowledge.schemas.knowledge import KnowledgeSearchOutput


@tool(
    description="搜索库存知识库，获取相关的采购规则和策略信息",
    response_format="content_and_artifact",
)
def search_smart_procurement_rules(query: str) -> tuple[str, dict]:
    """
    搜索库存知识库，获取相关的采购规则和策略信息

    Args:
        query: 要搜索的内容

    Returns:
        tuple[str, dict]: 模型可读的检索结果文本与结构化检索数据
    """
    chunks = BaseKnowledgeRetriever.search(
        collection_name="smart_procurement_rules", text=query, k=4
    )
    output = KnowledgeSearchOutput(query=query, chunks=chunks, total=len(chunks))
    if not chunks:
        return "未找到相关知识库内容", output.model_dump()

    visible_parts: list[str] = []
    for index, chunk in enumerate(chunks, 1):
        heading = f"{chunk.source} / {chunk.chapter_path}" if chunk.chapter_path else chunk.source
        visible_parts.append(
            f"[{index}] {heading}\n{chunk.content}"
        )

    return "\n---\n".join(visible_parts), output.model_dump()
