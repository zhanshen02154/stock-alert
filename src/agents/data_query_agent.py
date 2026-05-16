import time
from typing import Literal

from langchain.agents import create_agent
from langchain.agents.middleware import ToolRetryMiddleware
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.types import Command

from config.prompts.agents import get_agent_prompt
from src.core.agent_state import AgentState
from src.core.schemas import TaskInfo, AgentType
from src.tools.registry import ToolRegistry


def create_data_query_agent(llm: BaseChatModel):
    """
    创建数据查询Agent
    :param llm: 基础语言模型
    :return: 数据查询节点函数
    """
    tools = ToolRegistry.get_tools_by_group("tools_data_query")
    agent = create_agent(
        model=llm,
        tools=tools,
        system_prompt=SystemMessage(
            content=get_agent_prompt("data_query_agent", "system_message")
        ),
        middleware=[
            ToolRetryMiddleware(
                max_retries=3,
                backoff_factor=2.0,
                initial_delay=1.0,
                max_delay=30,
                jitter=True,
                tools=tools,
            ),
        ],
        state_schema=AgentState,
        name=AgentType.DATA_QUERY,
    )

    def create_data_query_node(
        state: AgentState,
    ) -> Command[Literal[AgentType.SUPERVISOR]]:
        """
        创建数据查询节点
        :param state: 状态
        :return: 包含查询数据的字典
        """
        task: TaskInfo = state.get("task")
        config: RunnableConfig = {"recursion_limit": 10}
        print("query params:", state)
        prompt = f"""
        请完成以下任务：
        当前任务描述: {task.description}
        """
        if task.timeliness:
            current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            prompt += f"\n时效要求: 是\n当前时间: {current_time}\n"
        else:
            prompt += "\n时效要求: 否\n"
        result = agent.invoke(
            {"messages": [HumanMessage(content=prompt)]},
            config=config,
        )
        print("query result:", result["messages"][-1])

        return Command(
            update={
                "messages": [result["messages"][-1]],
            },
            goto=AgentType.SUPERVISOR,
        )

    return create_data_query_node
