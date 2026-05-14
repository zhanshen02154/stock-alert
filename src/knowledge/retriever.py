import logging
from typing import Any, List

from langchain_core.embeddings import Embeddings
from pymilvus import Function, FunctionType, AnnSearchRequest

from src.knowledge.embedding import get_qwen_emeddings
from src.knowledge.vector_store import get_milvus_manager

logger = logging.getLogger(__name__)


def _default_rrf_reranker(k: int = 60) -> Function:
    """创建默认的 RRF 重排序器"""
    return Function(
        name="rrf",
        input_field_names=[],
        function_type=FunctionType.RERANK,
        params={"reranker": "rrf", "k": k},
    )


class BaseKnowledgeRetriever:
    """通用的检索器逻辑封装"""

    _embeddings: Embeddings | None = None
    _collections: dict[str, Any] = {}

    @classmethod
    def load(cls):
        cls._embeddings = get_qwen_emeddings()

    @classmethod
    def hybrid_search(cls, collection_name: str, text: str, k: int = 3) -> str:
        """
        混合搜索
        :param collection_name: 集合名称
        :param text: 文本
        :param k: 结果数量
        :return:
        """
        vector: list[float] = cls._embeddings.embed_query(text)
        ann_requests: List[AnnSearchRequest] = []
        params_1 = {
            "data": [text],
            "anns_field": "sparse_vector",
            "limit": k,
            "param": {"drop_ratio_search": 0.2},
        }
        params_2 = {
            "data": [vector],
            "anns_field": "dense_vector",
            "limit": k,
            "param": {"ef": 150},
        }
        ann_requests.append(AnnSearchRequest(**params_1))
        ann_requests.append(AnnSearchRequest(**params_2))

        results = get_milvus_manager().hybrid_search(
            collection_name=collection_name,
            ann_requests=ann_requests,
            search_kwargs={
                "ranker": _default_rrf_reranker(k=60),
            },
            k=k,
        )
        if len(results) == 0:
            return ""
        final_doc_list: list[str] = []
        for i, docs in enumerate(results):
            for j, item in enumerate(docs):
                final_doc_list.append(f"""
文档：{item["entity"]["document_title"]}
内容: {item["entity"]["text"]}
{item["entity"].get("text")}
""")
        return "\n--\n".join(final_doc_list)

    @classmethod
    def close(cls):
        cls._embeddings = None
        if cls._collections:
            cls._collections.clear()
