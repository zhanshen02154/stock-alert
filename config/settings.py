import json
import consul

configInfo = {}

class ConsulConfigLoader:
    def __init__(self,
                 host: str,
                 port: int,
                 scheme: str = "http"):
        self.host = host
        self.port = port
        self.scheme = scheme
        self.client = consul.Consul(host=self.host, port=self.port, scheme=self.scheme)

    def load_config(self, prefix: str):
        index, data = self.client.kv.get(prefix, recurse=False)
        if data is None:
            raise Exception(f"配置路径 'agent/stock-alert' 不存在")
        config = json.loads(data['Value'])
        global configInfo
        configInfo = config
        return config