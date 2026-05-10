from langgraph.graph import MessagesState


class AgentType:
    """
    Worker Agent类型
    """

    SUPERVISOR = "supervisor"  # supervisor
    DATA_QUERY = "data_query"  # 数据查询


class AgentState(MessagesState):
    user_input: str
    next: str
    summarized_messages: str
    interate_count: int
