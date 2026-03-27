import asyncio
import logging
import os
from typing import Optional
from dotenv import load_dotenv, set_key
from config import ConsulConfigLoader
from src.agents.inventory_agent import InventoryAgent
from src.core.llm import LLMClientFactory
from src.repository.session import create_session_repository
from src.service.session import create_session_service
from src.storage.mysql import create_mysql_session_store
from src.ui.gradio_app import create_gradio_app, GradioChatApp

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
        self.agent: Optional[InventoryAgent] = None
        self.gradio_app: Optional[GradioChatApp] = None
        self._shutdown_called = False
        self.mysql_store = None

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口，确保资源释放"""
        await self.shutdown()
        # 返回False让异常正常传播
        return False

    async def initialize(self):
        """初始化应用资源"""
        # 从Consul加载配置
        consul_host = os.getenv("CONSUL_HOST", "127.0.0.1")
        consul_port = int(os.getenv("CONSUL_PORT", "8500"))

        config_loader = ConsulConfigLoader(host=consul_host, port=consul_port)
        self.config = config_loader.load_config(prefix="agent/stock-alert")
        logger.info("配置加载完成")

        # 初始化LLM客户端
        LLMClientFactory.initialize(config=self.config.get("llm", {}))
        logger.info("LLM客户端初始化完成")

        # 创建数据库存储层
        self.mysql_store = create_mysql_session_store(
            config=self.config.get("mysql", {})
        )

        inventory_agent = InventoryAgent(
            agent_name="inventory",
            llm_config=self.config.get("agents").get("inventory", {})
        )
        session_service = create_session_service(
            session_repo=create_session_repository(session_store=self.mysql_store)
        )
        self.gradio_app = create_gradio_app(
            agent=inventory_agent,
            session_store=session_service
        )
        self.agent = inventory_agent

        self.mysql_store.initialize()
        self.gradio_app.start()

    async def shutdown(self):
        """优雅关闭应用"""
        if self._shutdown_called:
            return

        self._shutdown_called = True
        logger.info("开始优雅关闭应用...")

        # 1. 停止Gradio WebUI服务（等待后台任务完成）
        # if self.gradio_app:
        #     logger.info("停止Gradio应用...")
        #     await self.gradio_app.close()

        # 2. 关闭数据库连接池
        if self.mysql_store:
            logger.info("关闭数据库连接...")
            self.mysql_store.close()

        logger.info("应用关闭完成")

async def main():
    app = Application()

    try:
        # 初始化应用
        async with app:
            logger.info("应用初始化完成，启动Gradio服务器...")
            
            # 直接运行Gradio服务器（阻塞直到关闭）
            await app.gradio_app.serve()

    except KeyboardInterrupt:
        logger.info("收到键盘中断(Ctrl+C)，开始关闭...")
        await app.shutdown()
    except Exception as e:
        logger.error(f"应用运行异常: {e}", exc_info=True)
        await app.shutdown()
        raise
    finally:
        # 清理异步生成器
        loop = asyncio.get_event_loop()
        await loop.shutdown_asyncgens()
        logger.info("程序退出")

if __name__ == "__main__":
    asyncio.run(main())
