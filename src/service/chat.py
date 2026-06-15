import logging
import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass

from src.graph.inventory_manager import InventoryManagerGraph
from src.repository.session import SessionRepository
from src.utils.plain_text import sanitize_text

logger = logging.getLogger(__name__)


@dataclass
class SSEMessage:
    type: str
    content: str = ""
    message_id: str = ""
    full_content: str = ""


class ChatService:
    def __init__(
        self,
        agent: InventoryManagerGraph,
        session_repo: SessionRepository,
    ):
        self.__agent = agent
        self.__session_repo = session_repo

    def add_message(self, message: str, session_id: str, user_id: int) -> int:
        session_info = self.__session_repo.find_session_by_id(
            session_id=session_id, user_id=user_id
        )
        if not session_info:
            raise ValueError(f"会话不存在: {session_id}")
        msg_id = self.__session_repo.save_message(
            session_id=session_id, role="user", content=message
        )
        return msg_id

    async def chat_astream(
        self, session_id: str, user_id: int
    ) -> AsyncGenerator[SSEMessage]:
        """
        异步流式聊天
        :param session_id: 会话ID
        :param user_id: 用户ID
        :return: 异步生成器
        """
        message_id = str(uuid.uuid4())
        final_msg = ""
        try:
            msg_info = self.__session_repo.find_session_last_message(
                session_id=session_id
            )
            full_content = []
            user_message = sanitize_text(text=msg_info["content"])

            async for chunk in self.__agent.astream(
                message=user_message, thread_id=session_id, user_id=user_id
            ):
                if chunk.get("type") == "text":
                    full_content.append(chunk["text"])
                    yield SSEMessage(
                        type="chunk",
                        content=chunk["text"],
                        full_content="".join(full_content),
                        message_id=message_id,
                    )

            final_msg = "".join(full_content)
            yield SSEMessage(
                type="done",
                content=final_msg,
                full_content=final_msg,
                message_id=message_id,
            )
        except Exception as e:
            logger.error(e)
            final_msg = str(e)
            yield SSEMessage(type="error", content=str(e), message_id=message_id)
        finally:
            self.__session_repo.save_message(
                session_id=session_id, role="assistant", content=final_msg
            )
