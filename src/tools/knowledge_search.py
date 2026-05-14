from langchain_core.tools import tool

from src.knowledge.retriever import BaseKnowledgeRetriever


@tool(description="搜索库存知识库，获取相关的采购规则和策略信息")
def search_smart_procurement_rules(query: str) -> str:
    """
    搜索库存知识库，获取相关的采购规则和策略信息

    Args:
        query: 要搜索的内容

    Returns:
        str: 搜索结果字符串，包含相关文档内容
    """
    result = BaseKnowledgeRetriever.hybrid_search(
        collection_name="smart_procurement_rules", text=query, k=3
    )
    return result if result else "未找到相关知识库内容"
