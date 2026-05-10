from langchain_core.prompts import ChatPromptTemplate

INITIAL_SUMMARY_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("placeholder", "{messages}"),
        ("user", "请对上述对话进行总结:"),
    ]
)

EXISTING_SUMMARY_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("placeholder", "{messages}"),
        (
            "user",
            "这是迄今为止对话的总结: {existing_summary}\n\n"
            "通过考虑上述新消息来扩展此摘要:",
        ),
    ]
)

FINAL_SUMMARY_PROMPT = ChatPromptTemplate.from_messages(
    [
        # if exists
        ("placeholder", "{system_message}"),
        ("system", "到目前为止的对话总结: {summary}"),
        ("placeholder", "{messages}"),
    ]
)
