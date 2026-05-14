from typing import Literal

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.constants import END
from langgraph.types import Command

from config.prompts.system import SYSTEM_PROMPTS
from src.core.agent_state import AgentState
from src.core.schemas import Router, AgentType


def create_supervisor_agent(llm: BaseChatModel):
    """
    创建supervisor Agent
    :param llm: 大模型
    :return:
    """
    structed_llm = llm.with_structured_output(schema=Router)

    def supervisor_node(
        state: AgentState,
    ) -> Command[
        Literal[
            END,
            AgentType.DATA_QUERY,
            AgentType.SUPERVISOR,
            AgentType.KNOWLEDGE_SEARCH,
            AgentType.INVENTORY_OPERATOR,
            AgentType.SUPPLIER,
        ]
    ]:
        print("supervisor node:", state)
        prompt = ChatPromptTemplate.from_messages(
            [
                SystemMessage(content=SYSTEM_PROMPTS.get("supervisor")),
                MessagesPlaceholder(variable_name="summarized_messages"),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )
        chain = prompt | structed_llm
        result = chain.invoke(
            {
                "summarized_messages": state.get("summarized_messages"),
                "messages": state.get("messages"),
            }
        )
        print("supervisor result:", result)

        # 将 Router 对象转换为字典，避免序列化问题
        if isinstance(result, Router):
            result_dict = result.model_dump()
            goto = result_dict.get("next", "FINISH")
        else:
            goto = result.next if hasattr(result, "next") else "FINISH"

        if goto == "FINISH":
            goto = END

        return Command(
            update={"next": goto, "task": result.task},
            goto=goto,
        )

    return supervisor_node
