import time
from typing import Literal

from langchain.agents import create_agent
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.types import Command

from src import ToolRegistry
from src.core.agent_state import AgentState
from src.core.schemas import TaskInfo, AgentType


def create_supplier_agent(llm: BaseChatModel):
    """
    创建供应商智能体
    :param llm: 大模型
    :return:
    """

    tools = ToolRegistry.get_tools_by_group("tools_supplier_agent")

    system_prompt = """
    你是一个乐于助人的采购助手，擅长提供数据给其他协作者帮助他们完成任务。
    
    你可以使用的工具:
    获取商品的供应商信息
    """

    supplier_agent = create_agent(
        model=llm,
        name=AgentType.SUPPLIER,
        state_schema=AgentState,
        system_prompt=SystemMessage(content=system_prompt),
        tools=tools,
    )

    def supplier_agent_node(
        state: AgentState,
    ) -> Command[Literal[AgentType.SUPERVISOR]]:
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
        result = supplier_agent.invoke(
            {"messages": [HumanMessage(content=prompt)]},
            config=config,
        )
        print("supplier agent:", result["messages"][-1])

        return Command(
            update={
                "messages": [result["messages"][-1]],
            },
            goto=AgentType.SUPERVISOR,
        )

    return supplier_agent_node
