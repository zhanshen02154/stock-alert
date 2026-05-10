_VALID_MODELS = {
    "qwen": [
        "qwen-plus",
    ]
}


def validate_model(model: str, provider: str) -> bool:
    if provider not in _VALID_MODELS:
        return False

    if model in _VALID_MODELS[provider]:
        return True

    return False
