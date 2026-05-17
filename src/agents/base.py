import uuid

from langchain_core.messages import ToolMessage, AIMessage, ToolCall

_METADATA_KEY_IS_HANDOFF_BACK = "__is_handoff_back"


def create_handoff_back_messages(
    agent_name: str, supervisor_name: str
) -> tuple[AIMessage, ToolMessage]:
    """
    交接给Supervisor
    :param agent_name:
    :param supervisor_name:
    :return:
    """
    tool_call_id = str(uuid.uuid4())
    tool_name = f"transfer_back_to_{supervisor_name}"
    tool_calls = [ToolCall(name=tool_name, args={}, id=tool_call_id)]
    return (
        AIMessage(
            content=f"Transferring back to {supervisor_name}",
            tool_calls=tool_calls,
            name=agent_name,
            response_metadata={_METADATA_KEY_IS_HANDOFF_BACK: True},
        ),
        ToolMessage(
            content=f"Successfully transferred back to {supervisor_name}",
            name=tool_name,
            tool_call_id=tool_call_id,
            response_metadata={_METADATA_KEY_IS_HANDOFF_BACK: True},
        ),
    )
