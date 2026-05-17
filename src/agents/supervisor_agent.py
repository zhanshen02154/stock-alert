from typing import Literal

from langchain.agents import create_agent
from langchain.agents.middleware import SummarizationMiddleware
from langchain_core.language_models import BaseChatModel
from langfuse import observe
from langgraph.constants import END
from langgraph.types import Command

from config.prompts.summarization import DEFAULT_SUUMARIZATION_PROMPT
from config.prompts.system import SYSTEM_PROMPTS
from src.core.agent_state import AgentState
from src.core.schemas import Router, AgentType


def create_supervisor_agent(llm: BaseChatModel):
    """
    创建supervisor Agent
    :param llm: 大模型
    :return:
    """
    supervisor_agent = create_agent(
        model=llm,
        state_schema=AgentState,
        system_prompt=SYSTEM_PROMPTS.get("supervisor"),
        response_format=Router,
        middleware=[
            SummarizationMiddleware(
                model=llm,
                messages_to_keep=10,
                summary_prompt=DEFAULT_SUUMARIZATION_PROMPT,
                max_tokens_before_summary=4096,
            )
        ],
    )

    def _has_agent_answer(state: AgentState) -> bool:
        """检查是否已有子 agent 的回答（非 handoff 消息）"""
        for msg in reversed(state.get("messages", [])):
            if hasattr(msg, "name") and msg.name in (
                AgentType.KNOWLEDGES,
                AgentType.SUPPLY_CHAIN,
            ):
                if not msg.response_metadata.get("__is_handoff_back"):
                    return True
            if hasattr(msg, "type") and msg.type == "human":
                break
        return False

    @observe(capture_output=True, as_type="span")
    def supervisor_node(
        state: AgentState,
    ) -> Command[
        Literal[
            AgentType.SUPPLY_CHAIN,
            AgentType.KNOWLEDGES,
            END,
        ]
    ]:
        result = supervisor_agent.invoke({"messages": state.get("messages", [])})

        router: Router | None = result.get("structured_response", None)
        goto = router.next
        if goto == "FINISH":
            goto = END

        return Command(update={"next": goto, "task": router.next_task}, goto=goto)

    return supervisor_node
