import json
from typing import Any

import consul

GLOBAL_CONFIG = {}


class ConsulConfigLoader:
    def __init__(self, host: str, port: int, scheme: str = "http"):
        self.host = host
        self.port = port
        self.scheme = scheme
        self.client = consul.Consul(host=self.host, port=self.port, scheme=self.scheme)

    def load_config(self, prefix: str):
        index, data = self.client.kv.get(prefix, recurse=False)
        if data is None:
            raise Exception(f"配置路径 'agent/stock-alert' 不存在")
        config = json.loads(data["Value"])
        global GLOBAL_CONFIG
        GLOBAL_CONFIG = config
        return config


def get_llm_config(model_name: str) -> dict[str, Any]:
    """获取大模型配置"""
    return GLOBAL_CONFIG.get("llm", {}).get(model_name, {})


def get_agent_config(name: str) -> dict[str, Any]:
    """获取Agent配置"""
    return GLOBAL_CONFIG.get("agents", {}).get(name, {})


def get_storage_config(key: str) -> dict[str, Any]:
    """
    获取存储配置
    :param key:
    :return: 字典
    """
    return GLOBAL_CONFIG.get("storage", {}).get(key, {})


def get_checkpointer_config(key: str = "checkpointer") -> dict[str, Any]:
    return GLOBAL_CONFIG.get(key, {})


def get_graph_config() -> dict[str, Any]:
    """获取图配置"""
    return GLOBAL_CONFIG.get("graph", {})


def get_langfuse_config(key: str = "base") -> dict[str, Any]:
    return GLOBAL_CONFIG.get("langfuse", {}).get(key, {})


def get_prompt_manager_config() -> dict[str, Any]:
    return GLOBAL_CONFIG.get("prompt_manager", {})


def get_app_config(key: str):
    return GLOBAL_CONFIG.get("app", {}).get(key)


def get_app_env() -> str:
    app_env = get_app_config("environment")
    if app_env is None:
        app_env = "dev"
    return app_env
