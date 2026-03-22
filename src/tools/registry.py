# 注册工具
# 非必要请勿更改本文件

class ToolRegistry:
    def __init__(self):
        self._tools = {}

    def register(self, name: str):
     """工具装饰器"""
     def decorator(cls):
         tool_name = name or cls.__name__
         self._tools[tool_name] = cls
         return cls
     return decorator

    def get_tools(self, *args, **kwargs):
        """获取所有工具列表"""
        tools = []
        for tool_cls in self._tools.values():
            # 这里可以根据需要传递初始化参数
            try:
                tool_instance = tool_cls(*args, **kwargs)
                tools.append(tool_instance)
            except Exception as e:
                print(f"初始化工具 {tool_cls.__name__} 失败: {e}")
        return tools

    def get_tools_names(self):
        tool_names = []
        for tool_cls in self._tools.values():
            tool_names.append(tool_cls.__name__)
        return tool_names

# 创建全局注册器实例
tool_registry = ToolRegistry()