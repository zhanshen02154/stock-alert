import logging
import os
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import ConsulConfigLoader
from config.prompts import load_prompt_from_yaml, load_agent_prompts_from_yaml
from config.settings import get_graph_config, get_app_env
from src import ToolRegistry
from src.api.middleware import AuthMiddleware
from src.api.routers.chat import router as chat_router
from src.api.routers.health import router as health_router
from src.api.routers.user import routers as user_router
from src.core.prompt_manager import create_prompt_manager
from src.core.tracer import flush_langfuse, get_callback_handler, init_langfuse
from src.graph import InventoryManagerGraph
from src.knowledge import BaseKnowledgeRetriever
from src.knowledge.vector_store import load_milvus_manager, close_milvus_manager
from src.memory.checkpointer import CheckpointerFactory
from src.storage.mysql import init_mysql_session_store, close_mysql_session_store
from src.storage.redis import init_redis_client, close_redis_client, get_redis_client
from src.utils.api_client import HttpClient

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
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
        app_env = get_app_env()
        logger.info("配置加载完成")

        load_prompt_from_yaml(file_path="config/prompts/system.yaml")
        load_agent_prompts_from_yaml()
        logger.info("系统提示词加载完成")

        init_mysql_session_store()
        await init_redis_client()
        fastapp.state.redis_client = get_redis_client()

        # 注册所有工具
        ToolRegistry.init_tools()

        # 注册检查点
        await CheckpointerFactory.start(redis_client=get_redis_client().get_client())

        # 启动milvus
        load_milvus_manager()
        BaseKnowledgeRetriever.load()

        init_langfuse()

        create_prompt_manager()  # 创建提示词管理器

        # 启动LangGraph应用
        fastapp.state.inventory_graph = InventoryManagerGraph(
            debug=False,
            config=get_graph_config(),
            callbacks=[get_callback_handler()],
            environment=app_env,
        )
        fastapp.state.inventory_graph.setup_graph()

        logger.info("应用程序已经启动")

        yield
    finally:
        logger.info("应用关闭中")
        close_mysql_session_store()
        await close_redis_client()

        await HttpClient.close_all()

        await close_milvus_manager()
        BaseKnowledgeRetriever.close()

        # 关闭工具
        ToolRegistry.cleanup()

        if hasattr(fastapp.state, "kafka_consumer"):
            fastapp.state.kafka_consumer.stop()
            fastapp.state.kafka_consumer.close()

        if hasattr(fastapp.state, "inventory_graph"):
            await fastapp.state.inventory_graph.aclose()

        flush_langfuse()

        logger.info("应用已关闭")


app = FastAPI(title="智能库存Agent", lifespan=lifespan, root_path="/api/v1")
app.add_middleware(AuthMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://47.120.42.40:30023",
        "http://localhost:3000",
        "http://47.113.218.195:32251",
        "http://47.120.42.40:8080",
    ],
    allow_methods=["OPTIONS", "GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

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
