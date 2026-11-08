import os
from typing import Literal, Any

from config.settings import get_prompt_manager_config
from src.core.langfuse import get_langfuse_client


class PromptManager:
    """
    提示词管理器
    """
    def __init__(self, conf: dict[str, Any]):
        self._client = get_langfuse_client()
        self._env = os.environ.get(os.environ.get("ENV", "dev"))
        self._conf = conf
        if "prompt_cache_ttl" not in self._conf:
            self._conf["prompt_cache_ttl"] = 300

    def get_prompt_template_by_label(self,  name: str, prompt_type: Literal["chat", "text"] = "text", label: str = "latest"):
        """
        通过标签获取提示词模板
        """
        return self._client.get_prompt(name=name, label=label, type=prompt_type, cache_ttl_seconds=self._conf.get("prompt_cache_ttl"))

    def get_prompt_by_version(self, name: str, version: int, prompt_type: Literal["chat", "text"] = "text"):
        """
        通过版本获取提示词模板
        """
        return self._client.get_prompt(name=name, version=version, type=prompt_type, cache_ttl_seconds=self._conf.get("prompt_cache_ttl"))

    def render_and_track(self, prompt_name: str, variables: dict, trace_context=None):
        """
        渲染提示词并自动关联到当前 Trace
        :param prompt_name: 提示词名称
        :param variables: 模板变量字典
        :param trace_context: 当前的 trace/span 上下文（可选，装饰器会自动处理）
        """
        prompt_obj = self.get_prompt_template_by_label(prompt_name)
        if not prompt_obj:
            raise ValueError(f"Prompt {prompt_name} not found and no fallback available")

        # 执行模板渲染 (Langfuse prompt 对象通常支持 .compile 或直接字符串替换)
        # 假设 prompt_obj.prompt 是原始模板字符串
        rendered_prompt = prompt_obj.compile(**variables)

        return {
            "system": rendered_prompt,  # 根据实际模型结构调整
            "metadata": {
                "prompt_name": prompt_name,
                "prompt_version": prompt_obj.version,
                "prompt_id": prompt_obj.id
            }
        }


PromptManagerInstance: PromptManager | None = None

def load_prompt_manager():
    """
    加载提示词管理器
    """
    global PromptManagerInstance
    conf = get_prompt_manager_config()
    PromptManagerInstance = PromptManager(conf=conf)

def get_prompt_manager() -> PromptManager | None:
    """
    获取提示词管理器
    """
    global PromptManagerInstance
    if PromptManagerInstance is None:
        raise RuntimeError("提示词管理器未初始化")
    return PromptManagerInstance