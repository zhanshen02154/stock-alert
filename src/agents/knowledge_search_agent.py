import logging
from typing import Literal

from langchain.agents import create_agent
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import SystemMessage, ToolMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langfuse.decorators import observe
from langgraph.types import Command

from config.prompts.system import get_system_prompt
from src import ToolRegistry
from src.agents.base import create_handoff_back_messages
from src.core.agent_state import AgentState
from src.core.schemas import AgentType, TaskInfo

logger = logging.getLogger(__name__)


def create_knowledge_search_agent(llm: BaseChatModel):
    """
    创建知识库检索Agent
    :param llm: 大模型
    :return:
    """
    tools = ToolRegistry.get_tools_by_group("tools_knowledges")
    knowledge_search_agent = create_agent(
        model=llm,
        name=AgentType.KNOWLEDGES,
        state_schema=AgentState,
        system_prompt=SystemMessage(content=get_system_prompt("rag_system")),
        tools=tools,
    )

    @observe(capture_output=True, as_type="span")
    def knowledge_search_node(
        state: AgentState,
    ) -> Command[Literal[AgentType.SUPERVISOR]]:
        """
        知识库检索节点
        :param state: 状态
        :return: Command
        """
        config: RunnableConfig = {"recursion_limit": 10}
        task: TaskInfo = state.get("task")
        prompt = f"\n问题: {task.parameters.get("question")}"
        result = knowledge_search_agent.invoke(
            {"messages": [HumanMessage(content=prompt)]}, config=config
        )
        messages = result["messages"]
        if isinstance(messages[-1], ToolMessage):
            messages = messages[-2:]
        else:
            messages = messages[-1:]

        messages.extend(
            create_handoff_back_messages(AgentType.KNOWLEDGES, AgentType.SUPERVISOR)
        )
        return Command(
            update={
                "messages": messages,
                "completed_task": task,
            },
            goto=AgentType.SUPERVISOR,
        )

    return knowledge_search_node
