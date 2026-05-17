_VALID_MODELS = {
    "qwen": [
        "qwen-plus",
        "qwen3.6-plus",
        "qwen3.5-plus",
        "qwq-plus",
        "qwen3.5-plus-2026-04-20",
        "qwen3-14b",
    ],
    "deepseek": ["deepseek-r1"],
    "openai": ["openai/gpt-5.4"],
}


def validate_model(model: str, provider: str) -> bool:
    if provider not in _VALID_MODELS:
        return False

    if model in _VALID_MODELS[provider]:
        return True

    return False
