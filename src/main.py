import asyncio
import logging
import os
import signal
import threading
from typing import Optional

from config import ConsulConfigLoader
from src.agents.inventory_agent import InventoryAgent
from src.core.llm import LLMClientFactory
from src.events.consumer import create_consumer_from_config
from src.events.handlers import registry
from src.storage.session_store import MySQLSessionStore
from src.ui.gradio_app import create_gradio_app

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class Application:
    """应用程序主类"""

    def __init__(self):
        self.config: dict = {}
        self.session_store: Optional[MySQLSessionStore] = None
        self.agent: Optional[InventoryAgent] = None
        self.kafka_consumer = None
        self._shutdown_event = asyncio.Event()

    def initialize(self) -> None:
        """初始化应用（同步版本）"""
        # 从Consul加载配置
        consul_host = os.getenv("CONSUL_HOST", "127.0.0.1")
        consul_port = int(os.getenv("CONSUL_PORT", "8500"))
        
        config_loader = ConsulConfigLoader(host=consul_host, port=consul_port)
        self.config = config_loader.load_config(prefix="agent/stock-alert")
        logger.info("配置加载完成")

        # 初始化LLM客户端
        LLMClientFactory.initialize(config=self.config.get("llm", {}))
        logger.info("LLM客户端初始化完成")

        # 初始化MySQL会话存储
        mysql_config = self.config.get("mysql", {})
        if mysql_config:
            self.session_store = MySQLSessionStore(mysql_config)
            # 同步初始化
            asyncio.get_event_loop().run_until_complete(self.session_store.initialize())
            logger.info("MySQL会话存储初始化完成")
        else:
            logger.warning("未配置MySQL，会话存储功能不可用")

        # 初始化Agent
        self.agent = InventoryAgent("inventory", self.config.get("llm", {}))
        logger.info("Agent初始化完成")

    async def run_kafka_consumer(self) -> None:
        """运行Kafka消费者"""
        if "broker" not in self.config:
            logger.info("未配置broker，跳过Kafka消费者启动")
            return

        self.config['broker']['consumer']['hosts'] = self.config['broker']['hosts']
        self.kafka_consumer = create_consumer_from_config(config=self.config['broker']['consumer'])

        loop = asyncio.get_running_loop()

        def handle_shutdown():
            self._shutdown_event.set()
            if self.kafka_consumer:
                self.kafka_consumer.stop()

        # 注册信号处理
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(sig, handle_shutdown)
            except NotImplementedError:
                pass  # Windows不支持

        try:
            await self.kafka_consumer.start()
        finally:
            for sig in (signal.SIGINT, signal.SIGTERM):
                try:
                    loop.remove_signal_handler(sig)
                except NotImplementedError:
                    pass

    def run_gradio(self, server_name: str = "0.0.0.0", server_port: int = 7860) -> None:
        """运行Gradio界面"""
        if not self.agent:
            raise RuntimeError("Agent未初始化")
        
        if not self.session_store:
            raise RuntimeError("SessionStore未初始化，请检查MySQL配置")

        demo = create_gradio_app(
            agent=self.agent,
            # session_store=self.session_store,
            config=self.config
        )
        
        logger.info(f"启动Gradio服务: http://{server_name}:{server_port}")
        demo.launch(
            server_name=server_name,
            server_port=server_port,
            share=False,
            show_error=True,
            prevent_thread_lock=False
        )

    async def shutdown(self) -> None:
        """清理资源"""
        logger.info("正在关闭应用...")
        if self.session_store:
            await self.session_store.close()
        logger.info("应用已关闭")


def main() -> None:
    """主函数（同步版本）"""
    app = Application()
    
    try:
        app.initialize()
        
        # 获取运行模式
        mode = os.getenv("RUN_MODE", "gradio")  # gradio | kafka
        
        if mode == "gradio":
            # 仅运行Gradio
            app.run_gradio()
        elif mode == "kafka":
            # 仅运行Kafka消费者
            asyncio.run(app.run_kafka_consumer())
        elif mode == "both":
            # 同时运行：Kafka在后台线程
            def run_kafka():
                asyncio.run(app.run_kafka_consumer())
            
            kafka_thread = threading.Thread(target=run_kafka, daemon=True)
            kafka_thread.start()
            
            # 主线程运行Gradio
            app.run_gradio()
        else:
            logger.error(f"未知的运行模式: {mode}")
            
    except KeyboardInterrupt:
        logger.info("收到中断信号")
    except Exception as e:
        logger.error(f"应用运行错误: {e}", exc_info=True)
        raise
    finally:
        asyncio.run(app.shutdown())


if __name__ == "__main__":
    main()
