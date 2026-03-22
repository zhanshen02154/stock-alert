"""
Gradio聊天界面 - 与Agent交互（第一版：无历史对话）
"""
import logging
from typing import Optional, Dict, Any, List

import gradio as gr

from src.agents.inventory_agent import InventoryAgent

logger = logging.getLogger(__name__)


class GradioChatApp:
    """Gradio聊天应用"""

    def __init__(self, agent: InventoryAgent, config: Optional[Dict[str, Any]] = None):
        self.agent = agent
        self.config = config or {}

    async def chat(self, message: str) -> str:
        """
        处理聊天消息（第一版：无历史对话，直接调用Agent）
        
        Args:
            message: 用户消息
        """
        try:
            resp_list = self.agent.invoke(message)
            if isinstance(resp_list, list) and len(resp_list) > 0:
                # 取最后一条消息的内容
                return str(resp_list[0].get("content", ""))
            return "系统似乎遇到一些问题"
        except Exception as e:
            logger.error(f"聊天处理错误: {e}", exc_info=True)
            return f"抱歉，处理您的请求时出现错误: {str(e)}"

    def create_interface(self) -> gr.Blocks:
        """创建Gradio界面"""
        with gr.Blocks(
            title="库存助手",
            css="""
            .chat-container {max-width: 900px; margin: auto;}
            """
        ) as demo:
            gr.Markdown(
                """
                # 📦 智能库存助手
                与库存预警Agent进行对话，查询库存信息、设置预警规则等。
                """
            )
            
            # 聊天界面
            chatbot = gr.Chatbot(label="对话", height=500)
            
            with gr.Row():
                msg_input = gr.Textbox(
                    label="输入消息",
                    placeholder="请输入您的问题...",
                    scale=4,
                    show_label=False,
                    max_length=200
                )
                submit_btn = gr.Button("发送", scale=1, variant="primary")
            
            clear_btn = gr.Button("清空对话", variant="secondary")

            # 异步事件处理
            async def submit_message(message: str, history: List[List[str]]):
                if not message.strip():
                    return "", history
                response = await self.chat(message)
                user_msg = {"role": "user", "content": message}
                assistant_msg = {"role": "assistant", "content": response}
                return "", history + [user_msg, assistant_msg]

            def clear_chat():
                return [], ""

            # 绑定事件
            submit_btn.click(
                fn=submit_message,
                inputs=[msg_input, chatbot],
                outputs=[msg_input, chatbot]
            )
            
            msg_input.submit(
                fn=submit_message,
                inputs=[msg_input, chatbot],
                outputs=[msg_input, chatbot]
            )
            
            clear_btn.click(fn=clear_chat, outputs=[chatbot, msg_input])

        return demo


def create_gradio_app(
    agent: InventoryAgent,
    config: Optional[Dict[str, Any]] = None
) -> gr.Blocks:
    """
    创建Gradio应用
    
    Args:
        agent: Agent实例
        config: 配置
    
    Returns:
        Gradio Blocks应用
    """
    app = GradioChatApp(agent=agent, config=config)
    return app.create_interface()
