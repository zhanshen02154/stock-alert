from typing import Literal

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.prompts import MessagesPlaceholder, ChatPromptTemplate
from langgraph.constants import END
from langgraph.types import Command

from config.prompts.system import SYSTEM_PROMPTS
from src.core.agent_state import AgentState, AgentType
from src.core.schemas import Router


def create_supervisor_agent(llm: BaseChatModel):
    """
    创建supervisor Agent
    :param llm: 大模型
    :return:
    """
    structed_llm = llm.with_structured_output(schema=Router)

    def supervisor_node(
        state: AgentState,
    ) -> Command[Literal[END, AgentType.DATA_QUERY]]:
        state_msgs = state.get("messages", [])
        messages_for_prompt = list(state_msgs)
        if len(messages_for_prompt) == 0:
            human_msg = f"""
            # 用户输入
            {state.get("user_input")}
            """
            messages_for_prompt.append(HumanMessage(content=human_msg))
        prompt = ChatPromptTemplate.from_messages(
            [
                SystemMessage(content=SYSTEM_PROMPTS.get("supervisor")),
                MessagesPlaceholder(variable_name="summarized_messages"),
            ]
            + messages_for_prompt
        )
        chain = prompt | structed_llm
        result = chain.invoke(
            {"summarized_messages": state.get("summarized_messages", "无")}
        )
        
        # 将 Router 对象转换为字典，避免序列化问题
        if isinstance(result, Router):
            result_dict = result.model_dump()
            goto = result_dict.get("next", "FINISH")
        else:
            goto = result.next if hasattr(result, "next") else "FINISH"
            
        if goto == "FINISH":
            goto = END

        return Command(update={"next": goto}, goto=goto)

    return supervisor_node
