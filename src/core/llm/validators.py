_VALID_MODELS = {"qwen": ["qwen-plus", "qwen3.6-plus", "qwen3.5-plus", "qwq-plus"]}


def validate_model(model: str, provider: str) -> bool:
    if provider not in _VALID_MODELS:
        return False

    if model in _VALID_MODELS[provider]:
        return True

    return False
