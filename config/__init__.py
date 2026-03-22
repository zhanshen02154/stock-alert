"""配置模块"""
from typing import Any
from .settings import ConsulConfigLoader
import yaml
from pathlib import Path


def load_config_from_yaml(
    config_path: str | None = None
) -> dict[str, Any]:
    """
    从 YAML 文件加载配置
    
    Args:
        config_path: 配置文件路径，默认为 config/settings.yaml
        
    Returns:
        配置字典
    """
    if config_path is None:
        config_path = Path(__file__).parent / "settings.yaml"
    else:
        config_path = Path(config_path)
    
    if not config_path.exists():
        raise FileNotFoundError(f"配置文件不存在: {config_path}")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def load_config(
    consul_config: dict[str, Any] | None = None, 
    use_consul: bool = False
) -> dict[str, Any]:
    """
    加载配置（支持从 Consul 或本地 YAML 文件）
    
    Args:
        consul_config: Consul 配置信息
        use_consul: 是否使用 Consul 加载配置
        
    Returns:
        配置字典
    """
    if use_consul and consul_config:
        loader = ConsulConfigLoader(
            host=consul_config.get('host'),
            port=consul_config.get('port'),
            scheme=consul_config.get('scheme', 'http')
        )
        return loader.load_config(
            consul_config.get('config_prefix', 'agent/stock-alert')
        )
    else:
        return load_config_from_yaml()


__all__ = [
    'ConsulConfigLoader',
    'load_config_from_yaml',
    'load_config',
]
