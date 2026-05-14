import logging
from typing import Any

from langchain_core.language_models import BaseChatModel
from langgraph.constants import START
from langgraph.graph import StateGraph
from langgraph.store.mysql import PyMySQLStore
from langgraph.types import RetryPolicy
from langmem.short_term import SummarizationNode

from config.prompts.summarization import (
    INITIAL_SUMMARY_PROMPT,
    FINAL_SUMMARY_PROMPT,
    EXISTING_SUMMARY_PROMPT,
)
from src.agents.data_query_agent import create_data_query_agent
from src.agents.inventory_operate import create_inventory_operate_agent
from src.agents.knowledge_search_agent import create_knowledge_search_agent
from src.agents.supervisor_agent import (
    create_supervisor_agent,
)
from src.agents.suppliers_agent import create_supplier_agent
from src.core.agent_state import AgentState
from src.core.schemas import Context, AgentType
from src.memory.checkpointer import CheckpointerFactory
from src.storage.mysql import get_mysql_session_store
from src.storage.redis import create_async_redis_cache

logger = logging.getLogger(__name__)


class GraphSetup:
    """
    设置Graph
    """

    def __init__(self, llm: BaseChatModel, conf: dict[str, Any]):
        self.llm = llm
        self.graph = StateGraph(AgentState, context_schema=Context)
        self.supervisor_agent = create_supervisor_agent(llm=llm)
        self.query_agent = create_data_query_agent(llm=llm)
        self.knowledge_search_agent = create_knowledge_search_agent(llm=llm)
        self._inventory_operator = create_inventory_operate_agent(llm=llm)
        self._config = conf
        self.setup_graph()
        self.checkpointer = CheckpointerFactory.get_instance()
        self._cache = create_async_redis_cache()
        self._store = PyMySQLStore(conn=get_mysql_session_store().get_connection())
        self._store.setup()
        self.workflow = self.graph.compile(
            checkpointer=self.checkpointer,
            store=self._store,
        )

    def setup_graph(self):
        retry_conf = self._config.get("retry_policy", {})
        self.graph.add_node(
            "summarization",
            SummarizationNode(
                max_tokens=512,
                max_tokens_before_summary=1024,
                max_summary_tokens=128,
                model=self.llm,
                initial_summary_prompt=INITIAL_SUMMARY_PROMPT,
                existing_summary_prompt=EXISTING_SUMMARY_PROMPT,
                final_prompt=FINAL_SUMMARY_PROMPT,
            ),
        )
        self.graph.add_node(AgentType.SUPERVISOR, self.supervisor_agent)
        self.graph.add_node(
            AgentType.KNOWLEDGE_SEARCH,
            self.knowledge_search_agent,
        )
        self.graph.add_node(
            node=AgentType.DATA_QUERY,
            action=self.query_agent,
            retry_policy=RetryPolicy(
                **retry_conf,
                retry_on=(
                    ConnectionError,
                    TimeoutError,
                ),
            ),
        )
        self.graph.add_node(AgentType.INVENTORY_OPERATOR, self._inventory_operator)
        self.graph.add_node(AgentType.SUPPLIER, create_supplier_agent(llm=self.llm))
        self.graph.add_edge(START, "summarization")
        self.graph.add_edge("summarization", AgentType.SUPERVISOR)

    async def close(self):
        """
        关闭工作流
        :return:
        """
        self.workflow = None
        self.graph = None
        self.supervisor_agent = None
        self.query_agent = None
        self.checkpointer = None
        await self._cache.redis.aclose()
        self._store.conn.close()
        self._store = None
        self._cache = None

        logger.info("库存管理工作流已关闭")
