import logging
import os
from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import ConsulConfigLoader
from config.prompts import load_prompt_from_yaml
from src.api.routers.chat import router
from src.api.routers.health import router as health_router
from src.api.routers.user import routers as user_router
from src.api.routers.chat import router as chat_router
from src.api.middleware import AuthMiddleware
from src.core.llm import get_qwen_llm_client
from src.storage.mysql import create_mysql_session_store
from src.storage.redis import create_redis_client
from langgraph.checkpoint.redis import AsyncRedisSaver
from langgraph.checkpoint.memory import InMemorySaver
from config.settings import GLOBAL_CONFIG

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(fastapp: FastAPI):
    logger.info("应用程序启动中...")
    try:
        # 从Consul加载配置
        consul_host = os.getenv("CONSUL_HOST", "127.0.0.1")
        consul_port = int(os.getenv("CONSUL_PORT", "8500"))
        config_loader = ConsulConfigLoader(host=consul_host, port=consul_port)
        config_loader.load_config(prefix="agent/stock-alert")
        logger.info("配置加载完成")

        load_prompt_from_yaml(file_path="config/prompts/system.yaml")
        logger.info("系统提示词加载完成")

        fastapp.state.mysql_store = create_mysql_session_store()
        fastapp.state.redis_client = create_redis_client()
        await fastapp.state.redis_client.conn()  # 启动redis客户端

        # 创建checkpointer
        conf = GLOBAL_CONFIG.get("checkpointer", {})
        checkpointer_type = conf.get("type", "redis")
        if checkpointer_type == "redis":
            checkpointer = AsyncRedisSaver(redis_client=fastapp.state.redis_client.get_client())
            await checkpointer.setup()
            fastapp.state.checkpointer = checkpointer
        else:
            fastapp.state.checkpointer = InMemorySaver()

        # 创建大模型
        fastapp.state.qwen_llm = get_qwen_llm_client()

        logger.info("应用程序已经启动")

        yield
    finally:
        logger.info("应用关闭中")
        # 关闭MySQL连接
        if hasattr(fastapp.state, 'mysql_store'):
            fastapp.state.mysql_store.close()

        # 关闭Redis连接
        if hasattr(fastapp.state, 'redis_client'):
            await fastapp.state.redis_client.aclose()

        from src.api.dependencies import get_inventory_agent
        from src.agents.inventory_agent import InventoryAgent
        cached_agent: InventoryAgent | None = get_inventory_agent.cache.get((), None) if hasattr(get_inventory_agent,
                                                                                                 'cache') else None
        if cached_agent:
            await cached_agent.close()
        logger.info("应用已关闭")


app = FastAPI(title="智能库存预警Agent", lifespan=lifespan, root_path="/api/v1")
app.add_middleware(AuthMiddleware)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET", "POST", "OPTIONS", "PUT", "DELETE"],
                   allow_headers=["*"])
app.include_router(router=router)
app.include_router(router=health_router)
app.include_router(router=user_router)
app.include_router(router=chat_router)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  # 开发时可选，开启热重载
        log_level="info",
        timeout_graceful_shutdown=15
    )
