import requests


def create_http_client(api_key: str = "") -> requests.Session:
    """创建HTTP 客户端"""
    session = requests.session()
    if api_key:
        session.headers.update({"X-API-KEY": api_key})
    return session