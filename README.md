# 库存智能助手

[![Python](https://img.shields.io/badge/Python-3.13-blue.svg)](https://www.python.org/)
[![LangGraph](https://img.shields.io/badge/LangGraph-1.1.0-FF6B6B.svg)](https://langchain-ai.github.io/langgraph/)
[![LangChain](https://img.shields.io/badge/LangChain-1.2.12-FF6B6B.svg)](https://www.langchain.com/)
[![Milvus](https://img.shields.io/badge/Milvus-2.6.13-00D4FF.svg)](https://milvus.io/)

## 项目简介
库存智能助手是一个用于扩充库存系统能力的AI Agent，依托[商品服务](https://github.com/zhanshen02154/product)开发，进一步挖掘库存系统的价值，是[事件驱动微服务](https://github.com/zhanshen02154/go-micro-service)的附属产品。

该项目部署在 K8S 集群，配备全套自动化部署流程。全项目采用 supervisor 架构，Worker Agent 分为供应链 Agent 和知识库 Agent，负责执行和交接。该系统与后端 API 接口对接，可完成补货建议、库存查询、采购建议、补货申请等多种任务。

## 核心能力
- **Agent 架构设计：** 设计并实现 supervisor-worker 多 Agent 协作架构，解决了 supervisor 多轮对话中消息历史线性增长导致的上下文噪声问题，整合业务领域Worker 从**4** 个精简至**2** 个，大幅降低调度过程中往返supervisor节点的 token 消耗，初版输入+输出累计22K，现已减少到526-2.2K。
- **Prompt Engineering：** 结构化输出设计、混合提示词策略、上下文摘要压缩，有效控制 token 消耗。
- **RAG 知识库优化：** 混合搜索（HNSW + BM25）、数据清洗、相似度调优，通过 RAGAS + 人工双重评估，知识库召回率达86%。
- **系统稳定性保障：** 检查点机制、工具/节点重试策略、递归熔断保护，提升 Agent 自愈能力。
- **可观测性建设：** 集成 Langfuse 实现链路追踪，便于问题定位和后续优化。
- **可移植性设计：** Consul K/V 配置中心化 + ConfigMap 注入提示词，降低多环境部署的配置管理负担。
- **LLM 应用集成：** 集成 DashScope（通义千问）、OpenAI 多模型。

## 与langgraph-supervisor的区别

| 功能点                  | langgraph-supervisor | 本项目的supervisor架构 |
| ----------------------- | -------------------- | ---------------------- |
| Worker消息传输机制      | 全量传输             | 仅传递任务相关信息     |
| 上下文噪声              | √                    | ×                      |
| 可追溯性                | ×                    | √                      |
| 结构化输出              | ×                    | √                      |
| supervisor可控性        | ×                    | √（自由定制）          |
| 多意图任务token消耗成本 | 高                   | 低                     |

## 目录结构
```tree
│
├── config/                     # 配置文件
│   └── prompts/                # 提示词模板
│
├── docs/                       # 文档
│
├── src/                        # 源代码主目录
│   ├── agents/                 # Agent定义
│   ├── api/                    # API接口层
│   │   ├── middleware/         # 中间件
│   │   └── routers/            # 路由
│   ├── core/                   # 核心运行时与共享组件
│   │   └── llm/                # LLM模型封装
│   ├── events/                 # 事件处理层
│   │   ├── handlers/           # 事件处理器
│   │   └── protos/             # Protobuf定义
│   ├── graph/                  # LangGraph工作流
│   ├── knowledge/              # RAG知识库
│   ├── memory/                 # 记忆管理
│   ├── repository/             # 数据访问层
│   ├── service/                # 业务逻辑层
│   ├── storage/                # 存储层
│   ├── tools/                  # 工具
│   └── utils/                  # 通用工具函数
│
├── tests/                      # 测试
│
├── Dockerfile                  # Docker构建文件
├── docker-compose.yml          # Docker Compose配置
├── pyproject.toml              # 项目依赖配置
└── uv.lock                    # 依赖锁文件
```

## 技术选型
| 开发语言及工具 | 版本    | 用途                           |
| -------------- | ------- | ------------------------------ |
| kubernetes     | 1.23.1  | 容器编排                       |
| docker         | 20.10.7 | 容器运行                       |
| jenkins        | 2.346.1 | CI/CD                          |
| MySQL          | 8.0.45  | 持久层                         |
| Apisix         | 3.4.1   | API网关                        |
| harbor         | 1.8.6   | docker私有仓库                 |
| python         | 3.13.9  | 开发语言                       |
| Consul         | 1.7.3   | 服务注册/发现                  |
| Kafka          | 3.0.1   | 消息队列                       |
| langchain      | 1.2.12  | 开发框架                       |
| Milvus         | 2.6.13  | 向量数据库                     |
| langgraph      | 1.1.0   | 多智能体协作                   |
| RAGAS          | 0.4   | RAG评估                        |
| Redis          | 7.2     | 检查点、短期记忆、顶层应用缓存 |

## 大模型
- text-embedding-v4（嵌入模型）
- qwen-plus
- openai/gpt-5.4

## 本地开发指南
环境依赖：
- Docker 20.10.7+
- docker-compose

快速启动：
1. 复制配置：`cp docker-compose-dev.yml docker-compose.yml`，填写必要的环境变量
2. 构建镜像：`docker build -t stock-alert:local .`
3. 启动服务：`docker-compose up -d`

## 关键配置项（详见 docker-compose-dev.yml）
| 配置项            | 说明                     |
| ----------------- | ------------------------ |
| CONSUL_HOST       | Consul 服务地址          |
| MICROSERVICE_URL  | 后端微服务地址           |
| DASHSCOPE_API_KEY | 阿里云 DashScope API Key |
| JWT_SECRET_KEY    | JWT 密钥                 |
