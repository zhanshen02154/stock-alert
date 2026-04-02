import os
from functools import lru_cache

from langchain_core.language_models import ModelProfile, BaseChatModel
from langchain_openai import ChatOpenAI
from langchain_qwq import ChatQwen
from config.settings import get_llm_config


def get_qwen_llm_client() -> ChatQwen:
    """获取千问大模型客户端"""
    conf = get_llm_config("qwen")
    return ChatQwen(
        model=conf.get("model_name", "qwen-plus"),
        api_key=os.getenv("DASHSCOPE_API_KEY"),
        base_url=os.getenv("DASHSCOPE_API_BASE", "https://dashscope.aliyuncs.com/compatible-mode/v1"),
        temperature=conf.get("temperature", 0.1),
        timeout=conf.get("timeout", 60),
        max_retries=conf.get("max_retries", 3),
        max_tokens=conf.get("max_tokens", 4096),
        profile=ModelProfile(max_input_tokens=conf.get("max_input_tokens", 2048))
    )


def get_openai_client() -> ChatOpenAI:
    """获取OpenAI客户端"""
    conf = get_llm_config("openai")
    return ChatOpenAI(
        model=conf.get("model_name", "gpt-4o"),
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_API_BASE"),
        temperature=conf.get("temperature", 0.1),
        timeout=conf.get("timeout", 60),
        max_tokens=conf.get("max_tokens", 2048),
        max_retries=conf.get("max_retries", 3)
    )