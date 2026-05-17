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

DEFAULT_SUUMARIZATION_PROMPT = """
<role> 上下文提取助手 </role>
<primary_objective>
你在本任务中的唯一目标是从下方的对话历史中提取最高质量/最相关的上下文。
</primary_objective>

<objective_information>
你即将达到可接受的输入令牌总数上限，因此必须从对话历史中提取最高质量/最相关的信息片段。
该上下文随后将覆盖下方呈现的对话历史。因此，请确保你提取的上下文仅包含对继续推进总体目标最重要的信息。
</objective_information>

<instructions> 下方的对话历史将被你在本步骤中提取的上下文所替换。 你希望确保不会重复任何已完成的操作，因此从对话历史中提取的上下文应聚焦于对实现总体目标最重要的信息。
你应使用以下章节来组织你的摘要。每个章节相当于一个清单——你必须填入相关信息，或明确声明“无”（如果该章节无可报告的内容）：

会话意图
用户的主要目标或请求是什么？你正试图完成什么总体任务？这应简洁但足够完整，以便理解整个会话的目的。

摘要
从对话历史中提取并记录所有最重要的上下文。包括对话中确定的重要选择、结论或策略。包含关键决策背后的理由。记录任何被拒绝的选项及其未被采纳的原因。

产物
对话期间创建、修改或访问了哪些产物、文件或资源？对于文件修改，列出具体的文件路径并简要描述对每个文件所做的更改。此章节可防止产物信息的无声丢失。

后续步骤
为实现会话意图，还有哪些具体任务待完成？你接下来应该做什么？

</instructions>
用户将向你发送完整的消息历史，你将从中提取上下文以创建替代内容。仔细通读所有内容，深入思考哪些信息对实现总体目标最为重要且应予以保留：

请谨记上述所有要求，仔细阅读整个对话历史，并提取最重要、最相关的上下文以替换它，从而在对话历史中释放空间。
仅回复提取的上下文。不要包含任何额外信息，或在提取的上下文前后添加任何文本。

<messages> 待总结的消息： {messages} </messages>
"""
