import logging
import time
from typing import Literal

from langchain.agents import create_agent
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.types import Command

from config.prompts.system import get_system_prompt
from src import ToolRegistry
from src.core.agent_state import AgentState
from src.core.schemas import TaskInfo, AgentType

logger = logging.getLogger(__name__)


def create_knowledge_search_agent(llm: BaseChatModel):
    """
    创建知识库检索Agent
    :param llm: 大模型
    :return:
    """
    tools = ToolRegistry.get_tools_by_group("tools_knowledge_search")
    knowledge_search_agent = create_agent(
        model=llm,
        name=AgentType.KNOWLEDGE_SEARCH,
        state_schema=AgentState,
        system_prompt=SystemMessage(content=get_system_prompt("rag_system")),
        tools=tools,
    )

    def knowledge_search_node(
        state: AgentState,
    ) -> Command[Literal[AgentType.SUPERVISOR]]:
        """
        知识库检索节点
        :param state: 状态
        :return: Command
        """
        task: TaskInfo = state.get("task")
        config: RunnableConfig = {"recursion_limit": 5}
        prompt = f"""
        请完成以下任务：
        任务描述: {task.description}
        """
        if task.timeliness:
            current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            prompt += f"\n时效要求: 是\n当前时间: {current_time}\n"
        else:
            prompt += "\n时效要求: 否\n"

        print("knowledge_search_node", state)
        result = knowledge_search_agent.invoke(
            {"messages": [HumanMessage(content=prompt)]},
            config=config,
        )
        print("knowledge search result:", result["messages"][-1])

        return Command(
            update={
                "messages": [result["messages"][-1]],
            },
            goto=AgentType.SUPERVISOR,
        )

    return knowledge_search_node
