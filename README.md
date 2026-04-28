# 库存智能助手

## 项目简介
库存助手是一个可以用来操作库存系统的AI Agent，依托[商品服务](https://github.com/zhanshen02154/product)进行开发，进一步挖掘库存系统的价值，是[事件驱动微服务](https://github.com/zhanshen02154/go-micro-service)的
附属产品。

## 目录结构
```tree
├── config/                     # 配置文件
│   ├── __init__.py
│   ├── settings.py             # 应用主要配置（模型API地址、微服务URL、Kafka配置等）
│   └── prompts/                # 提示词模板集中管理
│
├── src/                        # 源代码主目录
│   ├── __init__.py
│   ├── main.py                 # 应用主入口，启动API服务和消费者
│   │
│   ├── core/                   # 核心运行时与共享组件
│   │   ├── __init__.py
│   │   ├── agent_state.py      # 定义LangGraph的State
│   │   ├── callbacks.py        # LangChain回调（用于日志、监控）
│   │   ├── exceptions.py       # 自定义异常
│   │   └── llm/                # LLM模型封装
│   │       ├── __init__.py
│   │       └── llm.py          # LLM客户端
│   │
│   ├── agents/                 # 各个Agent的定义
│   │
│   ├── api/                    # API接口层
│   │   ├── __init__.py
│   │   ├── dependencies.py     # 依赖注入
│   │   ├── schemas.py          # 请求/响应模型
│   │   ├── middleware/         # 中间件
│   │   │   ├── __init__.py
│   │   │   └── auth.py         # 认证中间件
│   │   └── routers/            # 路由
│   │       ├── __init__.py
│   │       ├── chat.py         # 聊天路由
│   │       ├── health.py       # 健康检查路由
│   │       └── user.py         # 用户路由
│   │
│   ├── events/                 # 事件处理层（与Kafka对接）
│   │   ├── __init__.py
│   │   ├── consumer.py         # 订阅Kafka主题
│   │   ├── decoder.py          # 事件解码器
│   │   ├── schemas.py          # 事件数据模型（Pydantic）
│   │   ├── handlers/           # 事件处理器
│   │   │   ├── __init__.py
│   │   └── protos/             # Protobuf定义
│   │
│   ├── knowledge/              # RAG知识库
│   │   ├── __init__.py
│   │   ├── embedding.py        # 嵌入模型
│   │   ├── retriever.py        # 检索器
│   │   ├── splitter.py         # 文本分割器
│   │   ├── vector_store.py     # 向量数据库客户端封装
│   │   ├── docs/               # 知识库文档
│   │   │   ├── security.md
│   │   │   └── 智能采购规则文档.md
│   │   └── schemas/            # 知识库数据模型
│   │       └── __init__.py
│   │
│   ├── repository/             # 数据访问层
│   │
│   ├── service/                # 业务逻辑层
│   │
│   ├── storage/                # 存储层
│   │   ├── __init__.py
│   │   ├── mysql.py            # MySQL连接
│   │   ├── redis.py            # Redis连接
│   │   └── session_store.py    # 会话存储
│   │
│   ├── tools/                  # 工具
│   │
│   └── utils/                  # 通用工具函数
│
├── tests/                      # 单元测试和集成测试
│   └── integration/            # 集成测试
│
├── scripts/                    # 实用脚本
├── Dockerfile                  # Docker构建文件
├── docker-compose.yml          # Docker Compose配置
├── pyproject.toml              # 项目依赖配置
└── uv.lock                    # 依赖锁文件
```

## 技术选型
| 开发语言及工具    | 版本      | 用途                 |
|------------|---------|--------------------|
| kubernetes | 1.23.1  | 容器编排               |
| docker     | 20.10.7 | 容器运行               |
| jenkins    | 2.346.1 | CI/CD              |
| MySQL      | 8.0.45  | 数据库                |
| Apisix     | 3.4.1   | API网关              |
| harbor     | 1.8.6   | docker私有仓库         |
| python     | 3.13.9  | 开发语言               |
| Consul     | 1.7.3   | 服务注册/发现            |
| Github     | -       | 代码托管和项目管理          |
| Kafka      | 3.0.1   | 收集Apisix日志、项目的核心组件 |
| langchain  | 1.2.12  | 开发框架               |
| Milvus     | 2.6.13  | 向量数据库              |


## 声明
- 请勿未经允许使用Releases的产物及源码用于商业用途，若需合作请发送邮件到zhanshen02154@gmail.com联系作者本人。
- 严禁将代码及产物（含附属品）用于非法活动如赌博、诈骗、洗钱等，一经发现将追究法律责任！