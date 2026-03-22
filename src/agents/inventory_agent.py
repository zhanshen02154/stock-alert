from typing import Optional, Dict, AsyncIterator, Any, List
from langchain.agents import create_agent
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.prompts import HumanMessagePromptTemplate, PromptTemplate

from src.agents.base_agent import BaseAgent
from src.core.llm import LLMClientFactory
from src.tools import QueryInventory
from src.tools.registry import tool_registry


class InventoryAgent(BaseAgent):
    """智能库存预警Agent"""
    system_msg: str = """
    你是一个库存助手，你需要使用工具帮助用户解决库存的问题。
    
    # 你可以使用的工具如下：
    - query_inventory: 查询库存信息
    """

    tools = []
    model: BaseChatModel = None

    def __init__(self, agent_name: str, llm_config: Optional[Dict] = None):
        super().__init__(agent_name=agent_name, llm_config=llm_config)
        self.tools = [QueryInventory()]
        self.model = LLMClientFactory.get_instance('qwq').client
        self._agent = create_agent(model=self.model, system_prompt=SystemMessage(content=self.system_msg), tools=self.tools)

    def invoke(self, message: str) -> List[dict[str, str]]:
        """
        同步调用Agent，返回最终结果
        
        Args:
            message: 用户输入消息
            
        Returns:
            Agent的响应文本
        """
        result = self._agent.invoke(messages=[HumanMessage(content=message)])
        final_msg = result["messages"][-1]

        if hasattr(final_msg, "content") and final_msg.content:
            return [{"role": "assistant", "content": final_msg.content}]

        return [{"role": "assistant", "content": "执行错误"}]

    async def astream(self, message: str) -> AsyncIterator[str]:
        """
        流式调用Agent，逐步返回响应
        
        Args:
            message: 用户输入消息
            
        Yields:
            Agent响应的文本片段
        """
        async for chunk in self._agent.astream({"messages": [{"role": "user", "content": message}]}):
            if "agent" in chunk and "messages" in chunk["agent"]:
                for msg in chunk["agent"]["messages"]:
                    if isinstance(msg, dict) and msg.get("content"):
                        yield msg["content"]
                    elif hasattr(msg, "content") and msg.content:
                        yield msg.content