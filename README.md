# 库存智能助手 (Stock Alert)

[![Python](https://img.shields.io/badge/Python-3.13-blue.svg)](https://www.python.org/)
[![LangGraph](https://img.shields.io/badge/LangGraph-1.1.0-FF6B6B.svg)](https://langchain-ai.github.io/langgraph/)
[![LangChain](https://img.shields.io/badge/LangChain-1.2.12-FF6B6B.svg)](https://www.langchain.com/)
[![Milvus](https://img.shields.io/badge/Milvus-2.6.13-00D4FF.svg)](https://milvus.io/)
[![Kafka](https://img.shields.io/badge/Kafka-3.0.1-231F20.svg)](https://kafka.apache.org/)

## 项目简介

基于 LangGraph 的多智能体库存管理 AI 系统。Supervisor Agent 负责意图识别与任务路由，将用户请求分发至 DataQuery Agent（数据查询）、Knowledge Search Agent（知识检索）、Inventory Operator Agent（库存操作）三个专用智能体。

核心技术亮点：
- **多智能体协作**：Supervisor + 3 个专用 Agent，基于 LangGraph 实现状态管理与流程编排
- **RAG 知识库**：Milvus 向量数据库 + 语义文档分割，实现库存知识精准检索
- **事件驱动架构**：Kafka 消息队列处理库存事件变更，事件溯源
- **状态持久化**：Redis Checkpointing + MySQL 会话存储，保障系统高可用

## 技术栈

| 分类           | 技术                 | 说明                    |
| -------------- | -------------------- | ----------------------- |
| **AI 框架**    | LangGraph 1.1.0      | 多智能体状态机编排      |
|                | LangChain 1.2.12     | LLM 接口抽象与工具调用  |
|                | RAGAS 1.1.0          | RAG 系统评估            |
| **向量数据库** | Milvus 2.6.13        | 知识库向量化存储与检索  |
| **消息队列**   | Kafka 3.0.1          | 库存事件异步处理        |
| **存储**       | MySQL 8.0.45         | 会话持久化              |
|                | Redis 7.2            | LangGraph 检查点 & 缓存 |
| **服务治理**   | Consul 1.7.3         | 配置中心与服务发现      |
| **LLM**        | DashScope (Qwen/QwQ) | 阿里通义千问系列        |
|                | OpenAI GPT 系列      | 备用模型                |

## 项目架构

```
FastAPI → ChatService → InventoryManagerGraph (LangGraph)
                                        ↓
                               SupervisorAgent (路由)
                              ↙        ↓         ↘
                    DataQuery  KnowledgeSearch  InventoryOperator
                       ↓             ↓               ↓
                    Tools        Milvus RAG        Tools
                       ↓                            ↓
                  Go Microservice              Go Microservice
```

## 快速开始

```bash
# 安装依赖
uv sync

# 启动应用
uv run python -m src.main

# 运行测试
uv run pytest tests/
```

## 目录结构

```
│
├── config/                     # 配置文件
│   └── prompts/                # Prompt 模板 (YAML)
│
├── docs/                       # 项目文档
│
├── scripts/                    # 实用脚本
│
├── sql/                        # SQL 脚本
│
├── src/                        # 源代码主目录
│   ├── agents/                 # Agent 定义
│   │   ├── supervisor_agent.py       # 任务路由与分发
│   │   ├── data_query_agent.py       # 数据查询 Agent
│   │   ├── knowledge_search_agent.py  # 知识检索 Agent
│   │   └── inventory_operate.py      # 库存操作 Agent
│   ├── api/                    # FastAPI 路由层
│   │   ├── middleware/         # 中间件
│   │   └── routers/            # API 路由
│   ├── core/                   # 核心运行时
│   │   ├── llm/                # LLM 工厂封装
│   │   └── AgentState.py       # LangGraph 状态定义
│   ├── events/                 # 事件处理层
│   │   ├── handlers/           # Kafka 事件处理器
│   │   └── protos/             # Protobuf 协议定义
│   ├── graph/                  # LangGraph 工作流
│   │   ├── inventory_manager.py      # 主流程编排
│   │   └── setup.py            # 图编译与策略配置
│   ├── knowledge/              # RAG 知识库
│   │   ├── Milvus 向量存储          # 向量数据库
│   │   └── semantic splitter         # 语义分割
│   ├── memory/                 # 记忆管理 (langmem)
│   ├── repository/             # 数据访问层 (MySQL)
│   ├── service/                # 业务逻辑层
│   ├── storage/                # 存储层
│   │   ├── mysql/              # MySQL 连接与会话
│   │   └── redis/              # Redis 检查点 & 缓存
│   ├── tools/                  # 工具注册与调用
│   │   └── registry.py         # 工具分组注册
│   └── utils/                  # 通用工具函数
│
├── tests/                      # 测试用例
│
├── Dockerfile                  # Docker 构建文件
├── docker-compose.yml          # Docker Compose 配置
├── pyproject.toml              # 项目依赖 (uv)
└── uv.lock                     # 依赖锁文件
```

## 核心模块说明

### Agent 层
- `supervisor_agent.py` - 意图识别与任务分发
- `data_query_agent.py` - 库存数据查询
- `knowledge_search_agent.py` - RAG 知识检索
- `inventory_operate.py` - 库存操作执行

### Graph 层
- `inventory_manager.py` - LangGraph 主流程编排
- `setup.py` - 节点重试/缓存策略配置

### Knowledge 层
- Milvus 向量存储 + 语义分割
- Retriever 实现动态知识库查询

---

## 声明

本项目仅供学习与个人求职使用，如需商务合作请联系 zhanshen02154@gmail.com。
