import json
from typing import Literal

from langchain.agents import create_agent
from langchain.agents.middleware import ToolRetryMiddleware
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import SystemMessage, ToolMessage, HumanMessage
from langgraph.types import Command

from config.prompts.agents import get_agent_prompt
from src.agents.base import create_handoff_back_messages, build_task_prompt
from src.core.agent_state import AgentState
from src.core.schemas import AgentType, TaskInfo, TaskResult
from src.tools.registry import ToolRegistry


def create_supply_chain_agent(llm: BaseChatModel):
    """
    创建数据查询Agent
    :param llm: 基础语言模型
    :return: 数据查询节点函数
    """
    tools = ToolRegistry.get_tools_by_group("tools_supply_chain")
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
        response_format=TaskResult,
        state_schema=AgentState,
        name=AgentType.SUPPLY_CHAIN,
    )

    def create_supply_chain_node(
        state: AgentState,
    ) -> Command[Literal[AgentType.SUPERVISOR]]:
        """
        创建数据查询节点
        :param state: 状态
        :return: 包含查询数据的字典
        """
        task: TaskInfo = state.get("task")
        print("query params:", task)
        prompt = (
            build_task_prompt(task)
            + f"\n商品SKU编号: {task.parameters.get("sku_code")}"
        )
        result = agent.invoke({"messages": [HumanMessage(content=prompt)]})
        print("query result:", result["messages"][-1])
        messages = result["messages"]
        if isinstance(messages[-1], ToolMessage):
            messages = messages[-2:]
        else:
            messages = messages[-1:]

        task_result: TaskResult | None = result.get("structured_response", None)
        if task_result is None:
            json_str = result["messages"][-1].content[0]["text"]
            data = json.loads(json_str)
            task_result = TaskResult(**data)

        messages.extend(
            create_handoff_back_messages(AgentType.SUPPLY_CHAIN, AgentType.SUPERVISOR)
        )

        print("supply_chain task_result => ", task_result)

        return Command(
            update={
                "messages": messages,
                "completed_task": [task],
                "finished_tasks": [task_result],
            },
            goto=AgentType.SUPERVISOR,
        )

    return create_supply_chain_node
