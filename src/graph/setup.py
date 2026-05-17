import logging
from typing import Any

from langchain_core.language_models import BaseChatModel
from langgraph.constants import START
from langgraph.graph import StateGraph
from langgraph.store.mysql import PyMySQLStore
from langgraph.types import RetryPolicy

from src.agents.data_query_agent import (
    create_supply_chain_agent,
)
from src.agents.knowledge_search_agent import create_knowledge_search_agent
from src.agents.supervisor_agent import (
    create_supervisor_agent,
)
from src.core.agent_state import AgentState
from src.core.schemas import Context, AgentType
from src.memory.checkpointer import CheckpointerFactory
from src.storage.mysql import get_mysql_session_store

logger = logging.getLogger(__name__)


class GraphSetup:
    """
    设置Graph
    """

    def __init__(self, llm: BaseChatModel, conf: dict[str, Any]):
        self.llm = llm
        self.graph = StateGraph(AgentState, context_schema=Context)
        self.supervisor_agent = create_supervisor_agent(llm=llm)
        self._supply_chain_agent = create_supply_chain_agent(llm=llm)
        self._knowledge_agent = create_knowledge_search_agent(llm=llm)
        self._config = conf
        self.setup_graph()
        self.checkpointer = CheckpointerFactory.get_instance()
        self._store = PyMySQLStore(conn=get_mysql_session_store().get_connection())
        self._store.setup()
        self.workflow = self.graph.compile(
            checkpointer=self.checkpointer,
            store=self._store,
        )

    def setup_graph(self):
        retry_conf = self._config.get("retry_policy", {})
        self.graph.add_node(AgentType.SUPERVISOR, self.supervisor_agent)
        self.graph.add_node(
            AgentType.KNOWLEDGES,
            self._knowledge_agent,
        )
        self.graph.add_node(
            node=AgentType.SUPPLY_CHAIN,
            action=self._supply_chain_agent,
            retry_policy=RetryPolicy(
                **retry_conf,
                retry_on=(
                    ConnectionError,
                    TimeoutError,
                ),
            ),
        )
        self.graph.add_edge(START, AgentType.SUPERVISOR)
        self.graph.set_entry_point(AgentType.SUPERVISOR)

    async def close(self):
        """
        关闭工作流
        :return:
        """
        self.workflow = None
        self.graph = None
        self.supervisor_agent = None
        self.checkpointer = None
        self._store.conn.close()
        self._store = None

        logger.info("库存管理工作流已关闭")
