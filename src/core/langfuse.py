import logging
import os

import httpx
from langfuse import Langfuse, get_client

logger = logging.getLogger(__name__)

def init_langfuse():
    Langfuse(public_key=os.environ.get("LANGFUSE_PUBLIC_KEY"),secret_key=os.environ.get("LANGFUSE_SECRET_KEY"),
                           base_url=os.environ.get("LANGFUSE_BASE_URL"),flush_at=10,flush_interval=5, timeout=30,
             httpx_client=httpx.Client(
                transport=httpx.HTTPTransport(local_address="0.0.0.0"),  # 强制走 IPv4 出连
                timeout=httpx.Timeout(10.0, connect=30.0),
                follow_redirects=True,
            ),
            environment=os.environ.get("ENV", "dev")
    )
    logger.info("Langfuse has been initialized")

def get_langfuse_client():
    return get_client()

def close_langfuse_client():
    """
    关闭Langfuse客户端
    """
    get_client().shutdown()
    logger.info("Langfuse has been closed")