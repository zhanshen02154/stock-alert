import yaml

SYSTEM_PROMPTS = {}

def load_prompt_from_yaml(file_path: str):
    """加载系统提示词"""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
        for key, value in data.items():
            SYSTEM_PROMPTS[key] = value