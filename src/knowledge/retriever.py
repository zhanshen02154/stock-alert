import hashlib
import logging
from typing import Any, List

from langchain_core.embeddings import Embeddings
from pymilvus import Function, FunctionType, AnnSearchRequest
from src.knowledge.embedding import get_qwen_emeddings
from src.knowledge.schemas.knowledge import KnowledgeChunk
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
    def search(cls, collection_name: str, text: str, k: int = 3) -> list[KnowledgeChunk]:
        """
        混合搜索
        :param collection_name: 集合名称
        :param text: 文本
        :param k: 结果数量
        :return: 结构化检索片段
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
            return []

        chunks: list[KnowledgeChunk] = []
        seen_chunk_ids: set[str] = set()
        for docs in results:
            for item in docs:
                entity = item.get("entity", {})
                content = entity.get("text", "")
                if not content:
                    continue
                source = entity.get("document_title", "")
                chapter_path = entity.get("chapter_path", "")
                chunk_id = str(entity.get("pk", "")) or hashlib.sha1(
                    f"{source}{chapter_path}{content}".encode("utf-8")
                ).hexdigest()
                if chunk_id in seen_chunk_ids:
                    continue
                seen_chunk_ids.add(chunk_id)
                chunks.append(
                    KnowledgeChunk(
                        chunk_id=chunk_id,
                        source=source,
                        version=str(entity.get("version", "") or "unknown"),
                        chapter_path=chapter_path,
                        content=content,
                        score=float(item.get("distance", 0.0) or 0.0),
                    )
                )

        chunks.sort(key=lambda chunk: chunk.score, reverse=True)
        return chunks

    @classmethod
    def close(cls):
        cls._embeddings = None
        if cls._collections:
            cls._collections.clear()
