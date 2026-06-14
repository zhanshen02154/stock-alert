from typing import Literal

from langchain.agents import create_agent
from langchain.agents.middleware import SummarizationMiddleware
from langchain.agents.middleware.types import (
    ResponseT,
    _InputAgentState,
    _OutputAgentState,
)
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage
from langgraph.constants import END
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import Command
from langgraph.typing import ContextT

from config.prompts.summarization import DEFAULT_SUUMARIZATION_PROMPT
from config.prompts.system import SYSTEM_PROMPTS
from src.core.agent_state import AgentState
from src.core.schemas import Router, AgentType, TaskResult, TaskInfo


def create_supervisor_agent(llm: BaseChatModel):
    """
    创建supervisor Agent
    :param llm: 大模型
    :return:
    """
    supervisor_agent: CompiledStateGraph[
        AgentState[ResponseT], ContextT, _InputAgentState, _OutputAgentState[ResponseT]
    ] = create_agent(
        model=llm,
        state_schema=AgentState,
        system_prompt=SYSTEM_PROMPTS.get("supervisor"),
        response_format=Router,
        middleware=[
            SummarizationMiddleware(
                model=llm,
                messages_to_keep=10,
                summary_prompt=DEFAULT_SUUMARIZATION_PROMPT,
                max_tokens_before_summary=2048,
            )
        ],
    )

    def supervisor_node(
        state: AgentState,
    ) -> Command[
        Literal[
            AgentType.SUPPLY_CHAIN,
            AgentType.KNOWLEDGES,
            END,
        ]
    ]:
        task_info: TaskInfo | None = state.get("task", None)
        finished_tasks = state.get("finished_tasks", [])
        last_task_result: TaskResult | None = None
        if len(finished_tasks) > 0:
            last_task_result = finished_tasks[-1]

        if last_task_result is not None and len(last_task_result.needs) > 0:
            prompt = f"""
            请根据以下信息，选择合适的助手继续执行任务，直到得到最终结果。
            当前时间戳（UTC+8）: {last_task_result.timestamp}
            用户问题: {state.get("user_input")}
            
            # 当前任务执行进度
            原始任务ID: {last_task_result.id}
            原始任务助手标识: {last_task_result.agent_type}
            原始任务执行结果: {last_task_result.result}
            原始任务所需的其他数据: {",".join(last_task_result.needs)}
            原始任务目标: {task_info.target}
            """
            result = supervisor_agent.invoke(
                {"messages": [HumanMessage(content=prompt)]}
            )
        else:
            result = supervisor_agent.invoke({"messages": state.get("messages", [])})

        router: Router | None = result.get("structured_response", None)
        goto = router.next
        if goto == "FINISH":
            goto = END

        return Command(update={"next": goto, "task": router.next_task}, goto=goto)

    return supervisor_node
