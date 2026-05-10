import yaml
import os
from pathlib import Path

# 定义Agent提示词全局变量
AGENT_PROMPTS = {}


def load_agent_prompts_from_yaml():
    """
    自动加载所有文件名以 '_agent' 结尾的 YAML 文件到 AGENT_PROMPTS 全局变量
    """
    # 获取当前文件所在目录（config/prompts/）
    prompts_dir = Path(__file__).resolve().parent
    
    # 查找所有以 '_agent.yaml' 结尾的文件
    agent_yaml_files = list(prompts_dir.glob("*_agent.yaml"))
    
    for yaml_file in agent_yaml_files:
        try:
            with open(yaml_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                
                # 使用文件名（不含扩展名）作为键
                agent_name = yaml_file.stem  # 例如: data_query_agent
                AGENT_PROMPTS[agent_name] = data
                
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"加载Agent提示词文件 {yaml_file} 失败: {str(e)}")
