# 库存智能助手

## 项目简介
库存助手是一个可以用来操作库存系统的AI Agent，依托[商品服务](https://github.com/zhanshen02154/product)进行开发，进一步挖掘库存系统的价值，是[事件驱动微服务](https://github.com/zhanshen02154/go-micro-service)的 附属产品。

## 目录结构
```tree
├── cli/                        # 命令行工具
│   ├── plugin/                 # 插件
│   └── skill/                  # 技能
│
├── config/                     # 配置文件
│   └── prompts/                # 提示词模板
│
├── docs/                       # 文档
│
├── scripts/                    # 实用脚本
│
├── sql/                        # SQL脚本
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
| 开发语言及工具    | 版本      | 用途              |
|------------|---------|-----------------|
| kubernetes | 1.23.1  | 容器编排            |
| docker     | 20.10.7 | 容器运行            |
| jenkins    | 2.346.1 | CI/CD           |
| MySQL      | 8.0.45  | 持久层             |
| Apisix     | 3.4.1   | API网关           |
| harbor     | 1.8.6   | docker私有仓库      |
| python     | 3.13.9  | 开发语言            |
| Consul     | 1.7.3   | 服务注册/发现         |
| Github     | -       | 代码托管和项目管理       |
| Kafka      | 3.0.1   | 消息队列            |
| langchain  | 1.2.12  | 开发框架            |
| Milvus     | 2.6.13  | 向量数据库           |
| langgraph  | 1.1.0   | 多智能体协作          |
| RAGAS      | 1.1.0   | RAG评估           |
| Redis      | 7.2     | 检查点、节点缓存、顶层应用缓存 |

## 大模型
- text-embedding-v4
- qwen3.5-plus
- ChatGPT 5.4
- DeepSeek-R1
- qwen3.6-plus

## 本地开发指南
- 安装Docker（Windows/Linux/Mac均可）。
- 将docker-compose-dev.yml复制到docker-compose.yml。
- 编译docker镜像为stock-alert:local。
- 运行命令
```bash
  docker-compose start
```

## 声明
- 请勿未经允许使用Releases的产物及源码用于商业用途，若需合作请发送邮件到zhanshen02154@gmail.com联系作者本人。
- 严禁将代码及产物（含附属品）用于非法活动如赌博、诈骗、洗钱等，一经发现将追究法律责任！