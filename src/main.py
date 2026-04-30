import logging
import os
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.redis import AsyncRedisSaver

from config import ConsulConfigLoader
from config.prompts import load_prompt_from_yaml
from config.settings import GLOBAL_CONFIG
from src.api.middleware import AuthMiddleware
from src.api.routers.chat import router
from src.api.routers.chat import router as chat_router
from src.api.routers.health import router as health_router
from src.api.routers.user import routers as user_router
from src.core.llm import get_qwen_llm_client
from src.knowledge.vector_store import load_milvus_manager, close_milvus_manager
from src.storage.mysql import create_mysql_session_store
from src.storage.redis import create_redis_client
from src.utils.api_client import ApiClientManager

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
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
        await fastapp.state.redis_client.conn()

        conf = GLOBAL_CONFIG.get("checkpointer", {})
        checkpointer_type = conf.get("type", "redis")
        if checkpointer_type == "redis":
            checkpointer = AsyncRedisSaver(
                redis_client=fastapp.state.redis_client.get_client()
            )
            await checkpointer.setup()
            fastapp.state.checkpointer = checkpointer
        else:
            fastapp.state.checkpointer = InMemorySaver()

        fastapp.state.qwen_llm = get_qwen_llm_client()

        load_milvus_manager()

        logger.info("应用程序已经启动")

        yield
    finally:
        logger.info("应用关闭中")
        if hasattr(fastapp.state, "mysql_store"):
            fastapp.state.mysql_store.close()

        if hasattr(fastapp.state, "redis_client"):
            await fastapp.state.redis_client.aclose()

        from src.api.dependencies import get_inventory_agent
        from src.agents.inventory_agent import InventoryAgent

        if hasattr(get_inventory_agent, "cache_clear"):
            get_inventory_agent.cache_clear()
        await ApiClientManager.close_all()
        logger.info("关闭API客户端")

        await close_milvus_manager()

        if hasattr(fastapp.state, "kafka_consumer"):
            fastapp.state.kafka_consumer.stop()
            fastapp.state.kafka_consumer.close()

        logger.info("应用已关闭")


app = FastAPI(title="智能库存Agent", lifespan=lifespan, root_path="/api/v1")
app.add_middleware(AuthMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://47.120.42.40:30023",
        "http://localhost:3000",
        "http://47.113.218.195:32251",
    ],
    allow_methods=["OPTIONS", "GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

app.include_router(router=router)
app.include_router(router=health_router)
app.include_router(router=user_router)
app.include_router(router=chat_router)

if __name__ == "__main__":
    uvicorn.run(
        app=app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        timeout_graceful_shutdown=15,
    )
