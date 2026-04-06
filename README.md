# 库存智能助手

## 项目简介
库存助手是一个可以用来操作库存系统的AI Agent，依托[商品服务](https://github.com/zhanshen02154/product)进行开发，进一步挖掘库存系统的价值，是[事件驱动微服务](https://github.com/zhanshen02154/go-micro-service)的
附属产品。

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
| python     | 3.13.9  | 智能体开发语言            |
| Consul     | 1.7.3   | 服务注册/发现            |
| Github     | -       | 代码托管和项目管理          |
| Kafka      | 3.0.1   | 收集Apisix日志、项目的核心组件 |
| langchain  | 1.2.12  | 智能体开发框架            |

## 声明
- 请勿未经允许使用Releases的产物及源码用于商业用途，若需合作请发送邮件到zhanshen02154@gmail.com联系作者本人。
- 严禁将代码及产物（含附属品）用于非法活动如赌博、诈骗、洗钱等，一经发现将追究法律责任！

## 前端流式传输信息
```json
{
   "type": "chunk",
  "content": "消息内容",
  "message_id": "消息ID",
  "full_content": "完整消息内容"
}
```

### 前端流式传输回调函数
```javascript
    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        console.log('SSE收到数据:', data)
        
        if (data.type === 'chunk') {
          onChunk(data.content, data.message_id, data.full_content)
        } else if (data.type === 'done') {
          onComplete(data.full_content, data.message_id)
          eventSource.close()
        } else if (data.type === 'error') {
          onError(data.message)
          eventSource.close()
        }
      } catch (error) {
        console.error('解析SSE数据失败:', error)
        onError('解析服务器响应失败')
      }
    }
```