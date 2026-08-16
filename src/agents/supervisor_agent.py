import logging
from typing import Literal

from langchain.agents import create_agent
from langchain.agents.middleware import SummarizationMiddleware
from langchain.agents.middleware.types import (
    ResponseT,
    _InputAgentState,
    _OutputAgentState,
)
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.constants import END
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import Command
from langgraph.typing import ContextT

from src.core.agent_state import AgentState
from src.core.prompt_manager import get_prompt_manager
from src.core.schemas import Router, AgentType, TaskInfo, TaskResult

logger = logging.getLogger(__name__)


def create_supervisor_agent(llm: BaseChatModel, env: str = "dev"):
    """
    创建supervisor Agent
    :param env: 环境
    :param llm: 大模型
    :return:
    """
    system_message = get_prompt_manager().get_prompt_by_environment(
        name="supervisor/system", label=env
    )
    summarization_prompt = get_prompt_manager().get_prompt_by_environment(
        "context_extraction_assistant", label=env
    )

    supervisor_agent: CompiledStateGraph[
        AgentState[ResponseT], ContextT, _InputAgentState, _OutputAgentState[ResponseT]
    ] = create_agent(
        model=llm,
        state_schema=AgentState,
        system_prompt=SystemMessage(content=system_message.prompt),
        response_format=Router,
        middleware=[
            SummarizationMiddleware(
                model=llm,
                messages_to_keep=10,
                summary_prompt=summarization_prompt.prompt,
                max_tokens_before_summary=4096,
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
            prompt = (
                get_prompt_manager()
                .get_prompt_by_environment("supervisor/need_others", label=env)
                .compile(
                    timestamp=last_task_result.timestamp,
                    user_input=state.get("user_input"),
                    task_id=last_task_result.id,
                    agent_type=last_task_result.agent_type,
                    result=last_task_result.result,
                    needs=",".join(last_task_result.needs),
                    target=task_info.target,
                )
            )
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
