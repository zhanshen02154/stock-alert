# 库存智能预警系统

## 目录结构
```tree
├── config/                 # 配置文件
│   ├── __init__.py
│   ├── settings.py         # 应用主要配置（模型API地址、微服务URL、Kafka配置等）
│   └── prompts/            # 提示词模板集中管理
│       ├── __init__.py
│       ├── monitor.yaml    # 监控Agent提示词
│       ├── decision.yaml   # 决策Agent提示词
│       └── emergency.yaml  # 紧急预警提示词
│
├── src/                    # 源代码主目录
│   ├── __init__.py
│   ├── main.py             # 应用主入口，启动消费者和Agent
│   │
│   ├── core/               # 核心运行时与共享组件
│   │   ├── __init__.py
│   │   ├── agent_state.py  # 定义LangGraph的State
│   │   ├── callbacks.py    # LangChain回调（用于日志、监控）
│   │   └── exceptions.py   # 自定义异常
│   │
│   ├── tools/              # **工具**
│   │
│   ├── agents/             # 各个Agent的定义
│   │   ├── __init__.py
│   │   ├── base_agent.py   # Agent基类
│   │   ├── monitor_agent.py    # 监控Agent
│   │   ├── decision_agent.py    # 决策Agent
│   │   └── orchestrator.py      # 多Agent编排器
│   │
│   ├── events/             # 事件处理层（与Kafka对接）
│   │   ├── __init__.py
│   │   ├── consumer.py     # 订阅“库存扣减成功”主题
│   │   ├── handler.py      # 事件处理器，路由到对应Agent
│   │   └── schemas.py      # 事件数据模型（Pydantic）
│   │
│   ├── knowledge/          # **RAG**
│   │   ├── __init__.py
│   │   ├── retriever.py    # 检索器
│   │   ├── vector_store.py # 向量数据库客户端封装（如Chroma）
│   │   └── documents/      # 存放知识库文档
│   │       └── inventory_policy.md
│   │
│   └── utils/              # 通用工具函数
│       ├── __init__.py
│       ├── api_client.py   # 封装Go微服务的HTTP调用
│       ├── logger.py       # 日志配置
│       └── formatters.py   # 数据格式化
│
├── tests/                  # 单元测试和集成测试

│
├── scripts/                # 实用脚本
│   ├── bootstrap.sh        # 环境初始化脚本
│   ├── start_agent.sh      # 启动Agent服务
│   └── load_test_data.py   # 加载测试数据
│
├── docker/                 # 容器化配置
│   ├── Dockerfile
│   └── docker-compose.yml  # 
│
├── docs/                   # 项目文档
│   ├── architecture.md     # 架构设计文档
│   ├── api_integration.md  # 与Go微服务的API对接文档
│   └── agent_workflow.md   # Agent处理流程图
│
```