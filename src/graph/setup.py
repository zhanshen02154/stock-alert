import logging
from typing import Any

from langchain_core.language_models import BaseChatModel
from langgraph.constants import START
from langgraph.graph import StateGraph
from langgraph.types import RetryPolicy
from langmem.short_term import SummarizationNode

from config.prompts.summarization import (
    INITIAL_SUMMARY_PROMPT,
    FINAL_SUMMARY_PROMPT,
    EXISTING_SUMMARY_PROMPT,
)
from src.agents.data_query_agent import create_data_query_agent
from src.agents.supervisor_agent import (
    create_supervisor_agent,
)
from src.core.agent_state import AgentState, AgentType
from src.memory.checkpointer import CheckpointerFactory

logger = logging.getLogger(__name__)


class GraphSetup:
    """
    设置Graph
    """

    def __init__(self, llm: BaseChatModel, conf: dict[str, Any]):
        self.llm = llm
        self.graph = StateGraph(AgentState)
        self.supervisor_agent = create_supervisor_agent(llm=llm)
        self.query_agent = create_data_query_agent(llm=llm)
        self._config = conf
        self.setup_graph()
        self.checkpointer = CheckpointerFactory.get_instance()
        self.workflow = self.graph.compile(checkpointer=self.checkpointer)

    def setup_graph(self):
        retry_conf = self._config.get("retry_policy", {})
        self.graph.add_node(
            "summarization",
            SummarizationNode(
                max_tokens=256,
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
        self.graph.add_edge(START, "summarization")
        self.graph.add_edge("summarization", AgentType.SUPERVISOR)

        logger.info("库存管理工作流已启动")

    def close(self):
        """
        关闭工作流
        :return:
        """
        self.workflow = None
        self.graph = None
        self.supervisor_agent = None
        self.query_agent = None
        self.checkpointer = None

        logger.info("库存管理工作流已关闭")
