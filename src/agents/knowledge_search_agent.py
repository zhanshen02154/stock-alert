import json
import logging
from typing import Literal

from langchain.agents import create_agent
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import SystemMessage, ToolMessage, HumanMessage
from langgraph.types import Command

from config.prompts.system import get_system_prompt
from src import ToolRegistry
from src.agents.base import create_handoff_back_messages, build_task_prompt
from src.core.agent_state import AgentState
from src.core.schemas import AgentType, TaskInfo, TaskResult

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
        response_format=TaskResult,
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
        prompt = build_task_prompt(task) + f"\n问题: {task.parameters.get("question")}"
        result = knowledge_search_agent.invoke(
            {"messages": [HumanMessage(content=prompt)]}
        )
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

        print("knowledge task result:", task_result)

        messages.extend(
            create_handoff_back_messages(AgentType.KNOWLEDGES, AgentType.SUPERVISOR)
        )
        return Command(
            update={
                "messages": messages,
                "completed_task": [task],
                "finished_tasks": [task_result],
            },
            goto=AgentType.SUPERVISOR,
        )

    return knowledge_search_node
