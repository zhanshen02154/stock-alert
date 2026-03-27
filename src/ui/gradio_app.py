"""
Gradio聊天界面 - 支持历史对话和会话管理
"""
import asyncio
import logging
import time
import uuid
from typing import Optional, Dict, Any, List, Tuple
import gradio as gr
import uvicorn
from dotenv import load_dotenv, set_key
from fastapi import FastAPI, status
from gradio.components.chatbot import ChatMessage

from src.agents.inventory_agent import InventoryAgent
from src.service.session import SessionService

logger = logging.getLogger(__name__)


class GradioChatApp:
    """Gradio聊天应用（支持历史对话）"""

    demo: gr.Blocks | None = None
    _started: bool = False
    app: FastAPI | None
    server: uvicorn.Server | None

    def __init__(
        self,
        agent: InventoryAgent,
        session_store: SessionService
    ):
        self.__agent = agent
        self.__session_store = session_store
        # 默认用户ID（匿名用户）
        self.__default_user_id = "anonymous"
        self.server = None

    async def chat_stream(self, message: str, session_id: str) -> str:
        """
        流式处理聊天消息，调用Agent

        Args:
            message: 用户消息
            session_id: 会话ID

        Yields:
            Agent响应的文本片段
        """
        try:
            resp_list = self.__agent.invoke(message, session_id)
            if isinstance(resp_list, list) and len(resp_list) > 0:
                # 取最后一条消息的内容
                return str(resp_list[0].get("content", ""))
            return "系统似乎遇到一些问题"
        except Exception as e:
            logger.error(f"聊天处理错误: {e}", exc_info=True)
            return f"抱歉，处理您的请求时出现错误: {str(e)}"

    def _generate_session_id(self) -> str:
        """生成唯一的会话ID"""
        return f"session_{int(time.time())}_{uuid.uuid4().hex[:8]}"

    def _extract_title(self, message: str, session_id: str = "", max_length: int = 20) -> str:
        """从消息中提取标题"""
        if not message:
            return "新对话"
        # 去除换行和多余空格
        if len(message) > max_length:
            return message[:max_length] + "..."
        return message

    def load_sessions(self) -> List[Tuple[str, str]]:
        """加载用户的所有会话列表，返回(session_id, title)列表"""
        try:
            sessions = self.__session_store.get_user_sessions(self.__default_user_id, 10)
            result = []
            for session in sessions:
                session_id = session["session_id"]
                metadata = session.get("metadata", {})
                title = metadata.get("title", "未命名对话")
                result.append((session_id, title))
            return result
        except Exception as e:
            logger.error(f"加载会话列表失败: {e}", exc_info=True)
            return []

    def load_session_history(self, session_id: str) -> List[ChatMessage]:
        """加载指定会话的历史消息，转换为Gradio Chatbot格式"""
        try:
            messages = self.__session_store.get_session_history(session_id)
            history = []
            for msg in messages:
                history.append(ChatMessage(content=msg["content"], role=msg["role"]))
            return history
        except Exception as e:
            logger.error(f"加载会话历史失败: {e}", exc_info=True)
            return []

    def save_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """保存消息到数据库"""
        try:
            self.__session_store.save_message(session_id, role, content, metadata)
        except Exception as e:
            logger.error(f"保存消息失败: {e}", exc_info=True)

    def create_new_session(self, title: str = "新对话") -> str:
        """创建新会话，返回session_id"""
        session_id = self._generate_session_id()
        metadata = {"title": title}
        try:
            self.__session_store.create_session(
                session_id=session_id,
                user_id=self.__default_user_id,
                metadata=metadata
            )
            logger.info(f"创建新会话: {session_id}, title: {title}")
        except Exception as e:
            logger.error(f"创建会话失败: {e}", exc_info=True)
        return session_id

    async def update_session_title(self, session_id: str, title: str) -> None:
        """更新会话标题，合并现有metadata"""
        try:
            # 获取现有metadata
            existing_metadata = {}
            sessions = self.__session_store.get_user_sessions(self.__default_user_id)
            for session in sessions:
                if session["session_id"] == session_id:
                    existing_metadata = session.get("metadata", {})
                    break
            
            # 合并metadata，优先使用新标题
            metadata = {**existing_metadata, "title": title}
            self.__session_store.update_session_metadata(session_id, metadata)
        except Exception as e:
            logger.error(f"更新会话标题失败: {e}", exc_info=True)

    async def _update_title_safe(self, session_id: str, title: str) -> None:
        """安全更新会话标题（捕获所有异常，用于即发即弃任务）"""
        try:
            await self.update_session_title(session_id, title)
            logger.info(f"会话标题已更新: {session_id} -> {title}")
        except Exception as e:
            # 仅记录错误，不抛出异常
            logger.error(f"更新会话标题失败（不影响主流程）: {e}", exc_info=True)

    def create_interface(self):
        """创建Gradio界面"""
        with gr.Blocks(
            title="库存助手",
            css="""
            .chat-container {max-width: 900px; margin: auto;}
            .session-sidebar {max-width: 300px; padding: 20px;}
            .session-item {padding: 10px; cursor: pointer; border-radius: 5px;}
            .session-item:hover {background-color: #f0f0f0;}
            """
        ) as demo:
            # 状态存储
            current_session_id = gr.State(value="")
            
            gr.Markdown(
                """
                # 📦 智能库存助手
                与库存预警Agent进行对话，查询库存信息、设置预警规则等。
                """
            )
            with gr.Row():
                # 左侧会话侧边栏
                with gr.Column(scale=1, min_width=300, elem_classes="session-sidebar"):
                    gr.Markdown("### 会话列表")
                    
                    # 会话列表（下拉选择）
                    session_dropdown = gr.Dropdown(
                        label="选择会话",
                        choices=[],
                        interactive=True,
                        allow_custom_value=False
                    )
                    
                    # 新建会话按钮
                    new_session_btn = gr.Button("新建会话", variant="primary")
                    
                    # 删除当前会话按钮
                    delete_session_btn = gr.Button("删除当前会话", variant="secondary")
                    
                    # 刷新会话列表按钮
                    refresh_btn = gr.Button("刷新列表", variant="secondary")
                    
                    gr.Markdown("---")
                    gr.Markdown("**说明：**")
                    gr.Markdown("- 点击「新建会话」开始新对话")
                    gr.Markdown("- 从列表中选择历史会话继续对话")
                    gr.Markdown("- 会话自动保存，可随时切换")
                
                # 右侧聊天区域
                with gr.Column(scale=3):
                    # 当前会话标题显示
                    session_title = gr.Markdown("### 当前会话：新对话")
                    
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
                    
                    clear_btn = gr.Button("清空当前对话", variant="secondary")
            
            # 初始化函数：加载会话列表并创建默认会话
            def initialize_app() -> Tuple[str, dict, str]:
                """初始化应用，返回默认session_id、下拉框更新和标题"""
                # 加载现有会话
                sessions = self.load_sessions()
                session_choices = [(title, sid) for sid, title in sessions]
                
                if sessions:
                    # 使用最近更新的会话
                    latest_session_id = sessions[0][0]
                    latest_title = sessions[0][1]
                    return (
                        latest_session_id,
                        gr.update(choices=session_choices, value=latest_session_id),
                        latest_title
                    )
                else:
                    # 创建新会话
                    new_session_id = self.create_new_session("新对话")
                    return (
                        new_session_id,
                        gr.update(choices=[], value=new_session_id),
                        "新对话"
                    )
            
            # 加载会话历史
            def load_selected_session(session_id: str) -> Tuple[List[List[str]], str, str]:
                """加载选中的会话历史"""
                if not session_id:
                    return [], "新对话", ""
                
                history = self.load_session_history(session_id)
                # 获取会话标题
                sessions = self.load_sessions()
                title = "新对话"
                for sid, t in sessions:
                    if sid == session_id:
                        title = t
                        break
                return history, title, session_id
            
            # 处理发送消息 - 流式输出
            async def submit_message(
                message: str,
                history: List[dict],
                session_id: str
            ) -> Tuple[str, List[List[str]], str, str]:
                """处理用户消息，保存到数据库并获取回复"""
                if not message.strip() or not session_id:
                    return "", history, session_id, ""

                # 保存用户消息
                self.save_message(session_id, "user", message)

                # 获取当前会话标题（用于返回）
                current_title = "新对话"
                try:
                    sessions = self.load_sessions()
                    for sid, title in sessions:
                        if sid == session_id:
                            current_title = title
                            break
                except Exception as e:
                    logger.error(f"获取会话标题失败: {e}", exc_info=True)

                # 如果是第一条消息，且当前标题为默认标题，则异步更新标题
                if not history and current_title == "新对话":
                    title = self._extract_title(message, session_id)
                    current_title = title  # 立即使用新标题
                    # 即发即弃：异步更新数据库中的标题，失败只记录日志
                    asyncio.create_task(
                        self._update_title_safe(session_id, title)
                    )

                # 调用Agent获取回复
                response = await self.chat_stream(message, session_id)

                # 保存助手回复
                self.save_message(session_id, "assistant", response)

                user_msg = {"role": "user", "content": message}
                assistant_msg = {"role": "assistant", "content": response}

                # 更新历史记录
                new_history = history + [user_msg, assistant_msg]

                # 清空输入框
                return "", new_history, session_id, current_title
            
            # 清空当前会话（仅清空界面，不删除数据库记录）
            def clear_current_chat() -> Tuple[List[List[str]], str]:
                return [], ""
            
            # 创建新会话
            def create_new_session_and_load() -> Tuple[str, dict, List[List[str]], str]:
                """创建新会话并加载到界面"""
                new_session_id = self.create_new_session("新对话")
                sessions = self.load_sessions()
                session_choices = [(title, sid) for sid, title in sessions]
                return (
                    new_session_id,
                    gr.update(choices=session_choices, value=new_session_id),
                    [],
                    "新对话"
                )
            
            # 删除当前会话
            def delete_current_session(
                session_id: str,
                current_sessions: List[Tuple[str, str]]
            ) -> Tuple[str, dict, List[List[str]], str]:
                """删除当前会话"""
                if not session_id:
                    return "", gr.update(choices=current_sessions, value=""), [], "新对话"
                
                try:
                    self.__session_store.delete_session(session_id)
                    logger.info(f"删除会话: {session_id}")
                except Exception as e:
                    logger.error(f"删除会话失败: {e}", exc_info=True)
                
                # 重新加载会话列表
                sessions = self.load_sessions()
                session_choices = [(title, sid) for sid, title in sessions]
                
                if sessions:
                    new_session_id = sessions[0][0]
                    new_title = sessions[0][1]
                    history = self.load_session_history(new_session_id)
                    return (
                        new_session_id,
                        gr.update(choices=session_choices, value=new_session_id),
                        history,
                        new_title
                    )
                else:
                    # 创建新会话
                    new_session_id = self.create_new_session("新对话")
                    return (
                        new_session_id,
                        gr.update(choices=[], value=new_session_id),
                        [],
                        "新对话"
                    )
            
            # 刷新会话列表
            def refresh_sessions() -> dict:
                """刷新会话列表"""
                sessions = self.load_sessions()
                session_choices = [(title, sid) for sid, title in sessions]
                return gr.update(choices=session_choices)
            
            # 绑定事件
            
            # 初始化
            demo.load(
                fn=initialize_app,
                outputs=[current_session_id, session_dropdown, session_title]
            )
            
            # 选择会话时加载历史
            session_dropdown.change(
                fn=load_selected_session,
                inputs=[session_dropdown],
                outputs=[chatbot, session_title, current_session_id]
            )
            
            # 发送消息
            submit_btn.click(
                fn=submit_message,
                inputs=[msg_input, chatbot, current_session_id],
                outputs=[msg_input, chatbot, current_session_id, session_title]
            )
            
            msg_input.submit(
                fn=submit_message,
                inputs=[msg_input, chatbot, current_session_id],
                outputs=[msg_input, chatbot, current_session_id, session_title]
            )
            
            # 清空当前对话
            clear_btn.click(
                fn=clear_current_chat,
                outputs=[chatbot, msg_input]
            )
            
            # 新建会话
            new_session_btn.click(
                fn=create_new_session_and_load,
                outputs=[current_session_id, session_dropdown, chatbot, session_title]
            )
            
            # 删除当前会话
            delete_session_btn.click(
                fn=delete_current_session,
                inputs=[current_session_id, session_dropdown],
                outputs=[current_session_id, session_dropdown, chatbot, session_title]
            )
            
            # 刷新会话列表
            refresh_btn.click(
                fn=refresh_sessions,
                outputs=[session_dropdown]
            )
            return demo

    async def close(self):
        """关闭Gradio应用"""
        if not self._started:
            return
        self._started = False
        
        # 关闭Agent（会自动关闭工具、数据库连接等）
        if self.__agent:
            self.__agent.close()
            logger.info("AI Agent已关闭")
        
        # 关闭Gradio演示
        if self.demo:
            self.demo.close()
            logger.info("Gradio界面已关闭")

    def start(self):
        """启动Gradio应用（仅初始化，不阻塞）"""
        if self._started:
            return
        self._started = True
        
        self.demo = self.create_interface()
        fastapi_app = FastAPI(title="AI Agent", description="AI Agent")
        fastapi_app.add_api_route("/health", self.health, methods=["GET"])
        fastapi_app.add_api_route("/readiness", self.readiness, methods=["GET"])
        self.app = gr.mount_gradio_app(fastapi_app, self.demo, path="/")
        
        # 配置uvicorn服务器
        config = uvicorn.Config(
            self.app, 
            host="0.0.0.0", 
            port=7860, 
            log_level="info",
            timeout_graceful_shutdown=30
        )
        self.server = uvicorn.Server(config)
        
        # 启动Agent
        self.__agent.start()
        logger.info("Agent启动完成，Gradio初始化完成")

    async def serve(self):
        """运行Gradio服务器（阻塞直到关闭）"""
        if not self.server:
            raise RuntimeError("服务器未初始化，请先调用start()")
        
        # 添加信号处理器
        import signal as sig_module
        loop = asyncio.get_running_loop()
        
        def handle_shutdown():
            logger.info("Gradio收到关闭信号")
            # 触发服务器关闭
            self.server.should_exit = True
            logger.info("已设置服务器关闭标志")
        
        # 注册信号处理器
        handlers_registered = []
        for sig in (sig_module.SIGINT, sig_module.SIGTERM):
            try:
                loop.add_signal_handler(sig, handle_shutdown)
                handlers_registered.append(sig)
                logger.debug(f"已注册信号处理器: {sig.name}")
            except NotImplementedError:
                pass

        try:
            logger.info("Gradio服务器启动中...")
            await self.server.serve()
        finally:
            # 确保资源清理
            await self.close()
            # 清理信号处理器
            for sig in handlers_registered:
                try:
                    loop.remove_signal_handler(sig)
                except (NotImplementedError, ValueError, KeyboardInterrupt):
                    pass
            logger.info("Gradio服务器已停止")

    async def health(self):
        if self._started:
            return {"status": "ok", "timestamp": time.time()}, status.HTTP_200_OK
        else:
            return {"status": "error", "message": "Agent is not started", "timestamp": time.time()}, status.HTTP_503_SERVICE_UNAVAILABLE

    async def readiness(self):
        if self._started:
            return {"status": "ok", "timestamp": time.time()}, status.HTTP_200_OK
        else:
            return {"status": "error", "message": "Agent is not started", "timestamp": time.time()}, status.HTTP_503_SERVICE_UNAVAILABLE

def create_gradio_app(
    agent: InventoryAgent,
    session_store: SessionService
) -> GradioChatApp:
    """
    创建Gradio应用（支持历史对话）

    Args:
        agent: Agent实例
        session_store: 会话存储实例

    Returns:
        Gradio聊天应用实例
    """
    return GradioChatApp(
        agent=agent,
        session_store=session_store
    )
