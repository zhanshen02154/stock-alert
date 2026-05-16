import time
from typing import Literal

from langchain.agents import create_agent
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.types import Command

from config.prompts.agents import get_agent_prompt
from src import ToolRegistry
from src.core.agent_state import AgentState
from src.core.schemas import TaskInfo, AgentType


def create_inventory_operate_agent(llm: BaseChatModel):
    """
    创建库存操作智能体
    :param llm: 大模型
    :return:
    """
    tools = ToolRegistry.get_tools_by_group("tools_inventory_operator")
    operate_agent = create_agent(
        model=llm,
        state_schema=AgentState,
        tools=tools,
        name=AgentType.INVENTORY_OPERATOR,
        system_prompt=SystemMessage(
            content=get_agent_prompt("inventory_operator_agent", "system_message")
        ),
    )

    def inventory_operate_node(
        state: AgentState,
    ) -> Command[Literal[AgentType.SUPERVISOR]]:
        task: TaskInfo = state.get("task")
        config: RunnableConfig = {"recursion_limit": 5}
        prompt = f"""
        请完成以下任务：
        当前任务描述: {task.description}
        """
        if task.timeliness:
            current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            prompt += f"\n时效要求: 是\n当前时间: {current_time}\n"
        else:
            prompt += "\n时效要求: 否\n"
        result = operate_agent.invoke(
            {"messages": [HumanMessage(content=prompt)]},
            config=config,
        )

        return Command(
            update={
                "messages": [result["messages"][-1]],
            },
            goto=AgentType.SUPERVISOR,
        )

    return inventory_operate_node
