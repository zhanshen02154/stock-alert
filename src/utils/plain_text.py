import re


def sanitize_text(text: str) -> str:
    """过滤文本中的特殊字符，只保留中文、英文、数字及常用标点"""
    return re.sub(
        r'[^\u4e00-\u9fff\u3000-\u303f\uff00-\uffefa-zA-Z0-9\s.,;:!?()（）、，。；：！？""'
        "·\-\—\/%\u00d7\u2190-\u21ff]",
        "",
        text,
    )
