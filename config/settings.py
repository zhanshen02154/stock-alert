import json
from typing import Any

import consul

GLOBAL_CONFIG = {}


class ConsulConfigLoader:
    def __init__(self,
                 host: str,
                 port: int,
                 scheme: str = "http"):
        self.host = host
        self.port = port
        self.scheme = scheme
        self.client = consul.Consul(host=self.host, port=self.port, scheme=self.scheme)

    def load_config(self, prefix: str):
        index, data = self.client.kv.get(prefix, recurse=False)
        if data is None:
            raise Exception(f"配置路径 'agent/stock-alert' 不存在")
        config = json.loads(data['Value'])
        global GLOBAL_CONFIG
        GLOBAL_CONFIG = config
        return config


def get_llm_config(model_name: str) -> dict[str, Any]:
    """获取大模型配置"""
    conf = GLOBAL_CONFIG.get("llm", {})
    if model_name in conf:
        return conf[model_name]
    return {}


def get_agent_config(name: str) -> dict[str, Any]:
    """获取Agent配置"""
    conf = GLOBAL_CONFIG.get("agents", {})
    if name in conf:
        return conf[name]
    return {}


def get_storage_config(key: str) -> dict[str, Any]:
    """获取存储配置"""
    conf = GLOBAL_CONFIG.get("storage", {})
    if key in conf:
        return conf[key]
    return {}
