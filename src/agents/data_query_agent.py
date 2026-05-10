from typing import Literal

from langchain.agents import create_agent
from langchain.agents.middleware import ToolRetryMiddleware
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import SystemMessage, AIMessage
from langgraph.types import Command

from config.prompts.agents import AGENT_PROMPTS
from src.core.agent_state import AgentType, AgentState
from src.tools import query_inventory
from src.tools.registry import ToolRegistry


def create_data_query_agent(llm: BaseChatModel):
    """
    创建数据查询Agent（使用LCEL链式调用）
    :param llm: 基础语言模型
    :return: 数据查询节点函数
    """
    tools = ToolRegistry.get_tools_by_group("tools_data_query")
    agent = create_agent(
        model=llm,
        tools=tools,
        system_prompt=SystemMessage(
            content=AGENT_PROMPTS.get("data_query_agent", {}).get("system_message")
        ),
        middleware=[
            ToolRetryMiddleware(
                max_retries=3,  # 最多重试 3 次
                backoff_factor=2.0,  # 指数回退乘数
                initial_delay=1.0,  # 从 1 秒延迟开始
                max_delay=30,  # 将延迟上限设置为 30 秒
                jitter=True,  # 添加随机抖动以避免"惊群"问题
                tools=[query_inventory],
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
        result = agent.invoke(state)

        return Command(
            update={
                "messages": [AIMessage(content=result["messages"][-1].content)],
            },
            goto=AgentType.SUPERVISOR,
        )

    return create_data_query_node
