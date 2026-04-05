import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from src.agents.inventory_agent import InventoryAgent
from src.repository.session import SessionRepository

@dataclass
class SSEMessage:
    type: str
    content: str = ""
    message_id: str = ""
    full_content: str = ""

class ChatService:
    def __init__(self, agent: InventoryAgent, session_repo: SessionRepository):
        self.__agent = agent
        self.__session_repo = session_repo

    def add_message(self, message: str, session_id: str, user_id: int) -> int:
        session_info = self.__session_repo.find_session_by_id(session_id=session_id, user_id=user_id)
        if not session_info:
            raise ValueError(f"会话不存在: {session_id}")
        msg_id = self.__session_repo.save_message(session_id=session_id, role="user", content=message)
        return msg_id

    async def chat_astream(self, session_id: str) -> AsyncGenerator[SSEMessage]:
        """
        异步流式聊天
        :param session_id: 会话ID
        :return: 异步生成器
        """
        try:
            msg_info = self.__session_repo.find_session_last_message(session_id=session_id)
            full_content = []
            message_id = str(uuid.uuid4())

            async for chunk in self.__agent.astream(message=msg_info['content'], thread_id=session_id):
                full_content.append(chunk['text'])  # 追加全部内容
                yield SSEMessage(type="chunk", content=chunk['text'], full_content="".join(full_content), message_id=message_id)

            final_msg = "".join(full_content)
            self.__session_repo.save_message(session_id=session_id, role="assistant", content=final_msg)

            yield SSEMessage(type="done", content=final_msg, full_content=final_msg, message_id=message_id)
        except Exception as e:
            yield SSEMessage(type="error", content=str(e))
